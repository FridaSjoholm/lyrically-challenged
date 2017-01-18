# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Manage parsing resource arguments for the cloud platform.

The Parse() function and Registry.Parse() method are to be used whenever a
Google Cloud Platform API resource is indicated in a command-line argument.
URLs, bare names with hints, and any other acceptable spelling for a resource
will be accepted, and a consistent python object will be returned for use in
code.
"""

import collections
import copy
import functools
import re
import types
import urllib

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

import uritemplate

_COLLECTION_SUB_RE = r'[a-zA-Z_]+(?:\.[a-zA-Z0-9_]+)+'

# The first two wildcards in this are the API and the API's version. The rest
# are parameters into a specific collection in that API/version.
_URL_RE = re.compile(r'(https?://[^/]+/[^/]+/[^/]+/)(.+)')
_METHOD_ID_RE = re.compile(r'(?P<collection>{collection})\.get'.format(
    collection=_COLLECTION_SUB_RE))
_GCS_URL_RE = re.compile('^gs://([^/]*)(?:/(.*))?$')
_GCS_URL = 'https://www.googleapis.com/storage/v1/'
_GCS_ALT_URL = 'https://storage.googleapis.com/'


class Error(Exception):
  """Exceptions for this module."""


class _ResourceWithoutGetException(Error):
  """Exception for resources with no Get method."""


class BadResolverException(Error):
  """Exception to signal that a resource has no Get method."""

  def __init__(self, param):
    super(BadResolverException, self).__init__(
        'bad resolver for [{param}]'.format(param=param))


class AmbiguousAPIException(Error):
  """Exception for when two APIs try to define a resource."""

  def __init__(self, collection, base_urls):
    super(AmbiguousAPIException, self).__init__(
        'collection [{collection}] defined in multiple APIs: {apis}'.format(
            collection=collection,
            apis=repr(base_urls)))


class AmbiguousResourcePath(Error):
  """Exception for when API path maps to two different resources."""

  def __init__(self, parser1, parser2):
    super(AmbiguousResourcePath, self).__init__(
        'There already exists parser {0} for same path, '
        'can not register another one {1}'.format(parser1, parser2))


class UserError(exceptions.Error, Error):
  """Exceptions that are caused by user input."""


class InvalidResourceException(UserError):
  """A collection-path that was given could not be parsed."""

  def __init__(self, line):
    super(InvalidResourceException, self).__init__(
        'could not parse resource: [{line}]'.format(line=line))


class WrongResourceCollectionException(UserError):
  """A command line that was given had the wrong collection."""

  def __init__(self, expected, got, path):
    super(WrongResourceCollectionException, self).__init__(
        'wrong collection: expected [{expected}], got [{got}], for '
        'path [{path}]'.format(
            expected=expected, got=got, path=path))
    self.got = got
    self.path = path


class UnknownFieldException(UserError):
  """A command line that was given did not specify a field."""

  def __init__(self, collection_name, expected):
    super(UnknownFieldException, self).__init__(
        'unknown field [{expected}] for [{collection_name}]'.format(
            expected=expected, collection_name=collection_name))


class UnknownCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, line):
    super(UnknownCollectionException, self).__init__(
        'unknown collection for [{line}]'.format(line=line))


class InvalidCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, collection):
    super(InvalidCollectionException, self).__init__(
        'unknown collection [{collection}]'.format(collection=collection))


class _ResourceParser(object):
  """Class that turns command-line arguments into a cloud resource message."""

  def __init__(self, params_defaults_func, collection_info):
    """Create a _ResourceParser for a given collection.

    Args:
      params_defaults_func: func(param)->value.
      collection_info: resource_util.CollectionInfo, description for collection.
    """
    self.params_defaults_func = params_defaults_func
    self.collection_info = collection_info

  def ParseRelativeName(
      self, relative_name, base_url=None, subcollection='', url_unescape=False):
    """Parse relative name into a Resource object.

    Args:
      relative_name: str, resource relative name.
      base_url: str, base url part of the api which manages this resource.
      subcollection: str, id of subcollection. See the api resource module
          (googlecloudsdk/third_party/apis/API_NAME/API_VERSION/resources.py).
      url_unescape: bool, if true relative name parameters will be unescaped.

    Returns:
      Resource representing this name.

    Raises:
      InvalidResourceException: if relative name doesn't match collection
          template.
    """
    path_template = self.collection_info.GetPathRegEx(subcollection)
    match = re.match(path_template, relative_name)
    if not match:
      raise InvalidResourceException(
          '{0} is not in {1} collection as it does not match path template {2}'
          .format(relative_name, self.collection_info.full_name, path_template))
    params = self.collection_info.GetParams(subcollection)
    fields = match.groups()
    if url_unescape:
      fields = map(urllib.unquote, fields)

    return Resource(self.collection_info, subcollection,
                    param_values=dict(zip(params, fields)),
                    endpoint_url=base_url)

  def ParseResourceId(self, resource_id, kwargs,
                      base_url=None, subcollection=''):
    """Given a command line and some keyword args, get the resource.

    Args:
      resource_id: str, Some identifier for the resource.
          Can be None to indicate all params should be taken from kwargs.
      kwargs: {str:(str or func()->str)}, flags (available from context) or
          resolvers that can help parse this resource. If the fields in
          collection-path do not provide all the necessary information,
          kwargs will be searched for what remains.
      base_url: use this base url (endpoint) for the resource, if not provided
          default corresponding api version base url will be used.
      subcollection: str, name of subcollection to use when parsing this path.

    Returns:
      protorpc.messages.Message, The object containing info about this resource.

    Raises:
      InvalidResourceException: If the provided collection-path is malformed.
      WrongResourceCollectionException: If the collection-path specified the
          wrong collection.
      UnknownFieldException: If the collection-path's path did not provide
          enough fields.
    """
    if resource_id is not None:
      try:
        return self.ParseRelativeName(
            resource_id, base_url=base_url, subcollection=subcollection)
      except InvalidResourceException:
        pass

    params = self.collection_info.GetParams(subcollection)
    fields = [None] * len(params)

    fields[-1] = resource_id

    param_values = dict(zip(params, fields))

    for param, value in param_values.items():
      if value is not None:
        continue

      # First try the resolvers given to this resource explicitly.
      resolver = kwargs.get(param)
      if resolver:
        param_values[param] = resolver() if callable(resolver) else resolver
      else:
        # Then try the registered defaults, can raise errors like
        # properties.RequiredPropertyError if property was tied to parameter.
        param_values[param] = self.params_defaults_func(param)

    ref = Resource(self.collection_info, subcollection, param_values,
                   base_url)
    return ref

  def __str__(self):
    path_str = ''
    for param in self.collection_info.params:
      path_str = '[{path}]/{param}'.format(path=path_str, param=param)
    return '[{collection}::]{path}'.format(
        collection=self.collection_info.full_name, path=path_str)


class Resource(object):
  """Information about a Cloud resource."""

  def __init__(self, collection_info, subcollection, param_values,
               endpoint_url):
    """Create a Resource object that may be partially resolved.

    To allow resolving of unknown params to happen after parse-time, the
    param resolution code is in this class rather than the _ResourceParser
    class.

    Args:
      collection_info: resource_util.CollectionInfo, The collection description
          for this resource.
      subcollection: str, id for subcollection of this collection.
      param_values: {param->value}, A list of values for parameters.
      endpoint_url: str, override service endpoint url for this resource. If
           None default base url of collection api will be used.
    Raises:
      UnknownFieldException: if param_values have None value.
    """
    self._collection_info = collection_info
    self._endpoint_url = endpoint_url or collection_info.base_url
    self._subcollection = subcollection
    self._path = collection_info.GetPath(subcollection)
    self._params = collection_info.GetParams(subcollection)
    for param, value in param_values.iteritems():
      if value is None:
        raise UnknownFieldException(collection_info.full_name, param)
      setattr(self, param, value)
    self._initialized = True

  def __setattr__(self, key, value):
    if getattr(self, '_initialized', None) is not None:
      raise NotImplementedError(
          'Cannot set attribute {0}. '
          'Resource references are immutable.'.format(key))
    super(Resource, self).__setattr__(key, value)

  def __delattr__(self, key):
    raise NotImplementedError(
        'Cannot delete attribute {0}. '
        'Resource references are immutable.'.format(key))

  def Collection(self):
    collection = self._collection_info.full_name
    if self._subcollection:
      return collection + '.' + self._subcollection
    return collection

  def GetCollectionInfo(self):
    return self._collection_info

  def Name(self):
    if self._params:
      # The last param is defined to be the resource's "name".
      return getattr(self, self._params[-1])
    return None

  def RelativeName(self, url_escape=False):
    """Relative resource name.

    A URI path ([path-noscheme](http://tools.ietf.org/html/rfc3986#appendix-A))
    without the leading "/". It identifies a resource within the API service.
    For example:
      "shelves/shelf1/books/book2"

    Args:
      url_escape: bool, if true would url escape each parameter.
    Returns:
       Unescaped part of SelfLink which is essentially base_url + relative_name.
       For example if SelfLink is
         https://pubsub.googleapis.com/v1/projects/myprj/topics/mytopic
       then relative name is
         projects/myprj/topics/mytopic.
    """
    escape_func = urllib.quote if url_escape else lambda x, safe: x

    effective_params = dict(
        [(k, escape_func(getattr(self, k), safe=''))
         for k in self._params])

    return urllib.unquote(
        uritemplate.expand(self._path, effective_params))

  def AsDict(self):
    """Returns resource reference parameters and its values."""
    return {k: getattr(self, k) for k in self._params}

  def SelfLink(self):
    """Returns URI for this resource."""
    self_link = '{0}{1}'.format(self._endpoint_url,
                                uritemplate.expand(self._path,
                                                   self.AsDict()))
    if (self._collection_info.api_name
        in ('compute', 'clouduseraccounts', 'storage')):
      # TODO(b/15425944): Unquote URLs for now for these apis.
      return urllib.unquote(self_link)
    return self_link

  def __str__(self):
    return self.SelfLink()

  def __eq__(self, other):
    if isinstance(other, Resource):
      return self.SelfLink() == other.SelfLink()
    return False


def _CopyNestedDictSpine(maybe_dictionary):
  if type(maybe_dictionary) is types.DictType:
    result = {}
    for key, val in maybe_dictionary.iteritems():
      result[key] = _CopyNestedDictSpine(val)
    return result
  else:
    return maybe_dictionary


def _APINameFromCollection(collection):
  """Get the API name from a collection name like 'api.parents.children'.

  Args:
    collection: str, The collection name.

  Returns:
    str: The API name.
  """
  return collection.split('.')[0]


class Registry(object):
  """Keep a list of all the resource collections and their parsing functions.

  Attributes:
    parsers_by_collection: {str: {str: {str: _ResourceParser}}}, All the
        resource parsers indexed by their api name, api version
        and collection name.
    parsers_by_url: Deeply-nested dict. The first key is the API's URL root,
        and each key after that is one of the remaining tokens which can be
        either a constant or a parameter name. At the end, a key of None
        indicates the value is a _ResourceParser.
    default_param_funcs: Triply-nested dict. The first key is the param name,
        the second is the api name, and the third is the collection name. The
        value is a function that can be called to find values for params that
        aren't specified already. If the collection key is None, it matches
        all collections.
    registered_apis: {str: list}, All the api versions that have been
        registered, in order of registration.
        For instance, {'compute': ['v1', 'beta', 'alpha']}.
  """

  def __init__(self, parsers_by_collection=None, parsers_by_url=None,
               default_param_funcs=None, registered_apis=None):
    self.parsers_by_collection = parsers_by_collection or {}
    self.parsers_by_url = parsers_by_url or {}
    self.default_param_funcs = default_param_funcs or {}
    self.registered_apis = registered_apis or collections.defaultdict(list)

  def Clone(self):
    """Fully clones this registry."""
    reg = Registry(
        parsers_by_collection=_CopyNestedDictSpine(self.parsers_by_collection),
        parsers_by_url=_CopyNestedDictSpine(self.parsers_by_url),
        default_param_funcs=_CopyNestedDictSpine(self.default_param_funcs),
        registered_apis=copy.deepcopy(self.registered_apis))
    for _, version_collections in reg.parsers_by_collection.iteritems():
      for _, collection_parsers in version_collections.iteritems():
        for _, parser in collection_parsers.iteritems():
          parser.params_defaults_func = functools.partial(
              reg.GetParamDefault,
              parser.collection_info.api_name,
              parser.collection_info.name)

    def _UpdateParser(dict_or_parser):
      if type(dict_or_parser) is types.DictType:
        for _, val in dict_or_parser.iteritems():
          _UpdateParser(val)
      else:
        _, parser = dict_or_parser
        parser.params_defaults_func = functools.partial(
            reg.GetParamDefault,
            parser.collection_info.api_name,
            parser.collection_info.name)
    _UpdateParser(reg.parsers_by_url)
    return reg

  def RegisterApiByName(self, api_name, api_version=None):
    """Register the given API if it has not been registered already.

    Args:
      api_name: str, The API name.
      api_version: if available, the version of the API being registered.
    Returns:
      api version which was registered.
    """
    registered_versions = self.registered_apis.get(api_name, [])
    if api_version in registered_versions:
      # This API version has been registered.
      registered_versions.remove(api_version)
      registered_versions.append(api_version)
      return api_version
    if api_version is None:
      if registered_versions:
        # Use last registered api version as default.
        return registered_versions[-1]
      api_version = core_apis.GetDefaultVersion(api_name)

    for collection in core_apis.GetApiCollections(api_name, api_version):
      self._RegisterCollection(collection)

    self.registered_apis[api_name].append(api_version)
    return api_version

  def _RegisterCollection(self, collection_info):
    """Registers given collection with registry.

    Args:
      collection_info: CollectionInfo, description of resource collection.
    Raises:
      AmbiguousAPIException: If the API defines a collection that has already
          been added.
      AmbiguousResourcePath: If api uses same path for multiple resources.
    """
    api_name = collection_info.api_name
    api_version = collection_info.api_version
    parser = _ResourceParser(
        functools.partial(self.GetParamDefault, api_name, collection_info.name),
        collection_info)

    collection_parsers = (self.parsers_by_collection.setdefault(api_name, {})
                          .setdefault(api_version, {}))
    collection_subpaths = collection_info.flat_paths
    if not collection_subpaths:
      collection_subpaths = {'': collection_info.path}

    for subname, path in collection_subpaths.iteritems():
      collection_name = collection_info.full_name + (
          '.' + subname if subname else '')
      existing_parser = collection_parsers.get(collection_name)
      if existing_parser is not None:
        raise AmbiguousAPIException(collection_name,
                                    [collection_info.base_url,
                                     existing_parser.collection_info.base_url])
      collection_parsers[collection_name] = parser

      self._AddParserForUriPath(api_name, api_version, subname, parser, path)

  def _AddParserForUriPath(self, api_name, api_version,
                           subcollection, parser, path):
    """Registers parser for given path."""
    tokens = [api_name, api_version] + path.split('/')

    # Build up a search tree to match URLs against URL templates.
    # The tree will branch at each URL segment, where the first segment
    # is the API's base url, and each subsequent segment is a token in
    # the instance's get method's relative path. At the leaf, a key of
    # None indicates that the URL can finish here, and provides the parser
    # for this resource.
    cur_level = self.parsers_by_url
    while tokens:
      token = tokens.pop(0)
      if token[0] == '{' and token[-1] == '}':
        token = '{}'
      if token not in cur_level:
        cur_level[token] = {}
      cur_level = cur_level[token]
    if None in cur_level:
      raise AmbiguousResourcePath(cur_level[None], parser)

    cur_level[None] = subcollection, parser

  def SetParamDefault(self, api, collection, param, resolver):
    """Provide a function that will be used to fill in missing values.

    Args:
      api: str, The name of the API that func will apply to.
      collection: str, The name of the collection that func will apploy to. Can
          be None to indicate all collections within the API.
      param: str, The param that can be satisfied with func, if no value is
          provided by the path.
      resolver: str or func()->str, A function that returns a string or raises
          an exception that tells the user how to fix the problem, or the value
          itself.

    Raises:
      ValueError: If api or param is None.
    """
    if not api:
      raise ValueError('provided api cannot be None')
    if not param:
      raise ValueError('provided param cannot be None')
    if param not in self.default_param_funcs:
      self.default_param_funcs[param] = {}
    api_collection_funcs = self.default_param_funcs[param]
    if api not in api_collection_funcs:
      api_collection_funcs[api] = {}
    collection_funcs = api_collection_funcs[api]
    collection_funcs[collection] = resolver

  def GetParamDefault(self, api, collection, param):
    """Return the default value for the specified parameter.

    Args:
      api: str, The name of the API that param is part of.
      collection: str, The name of the collection to query. Can be None to
          indicate all collections within the API.
      param: str, The param to return a default for.

    Raises:
      ValueError: If api or param is None.

    Returns:
      The default value for a parameter or None if there is no default.
    """
    if not api:
      raise ValueError('provided api cannot be None')
    if not param:
      raise ValueError('provided param cannot be None')
    api_collection_funcs = self.default_param_funcs.get(param)
    if not api_collection_funcs:
      return None
    collection_funcs = api_collection_funcs.get(api)
    if not collection_funcs:
      return None
    if collection in collection_funcs:
      resolver = collection_funcs[collection]
    elif None in collection_funcs:
      resolver = collection_funcs[None]
    else:
      return None
    return resolver() if callable(resolver) else resolver

  def _GetParserForCollection(self, collection):
    # Register relevant API if necessary and possible
    api_name = _APINameFromCollection(collection)
    api_version = self.RegisterApiByName(api_name)

    parser = (self.parsers_by_collection
              .get(api_name, {}).get(api_version, {}).get(collection, None))
    if parser is None:
      raise InvalidCollectionException(collection)
    return parser

  def ParseResourceId(self, collection, resource_id, kwargs):
    """Parse a resource id string into a Resource.

    Args:
      collection: str, the name/id for the resource from commandline argument.
      resource_id: str, Some resouce identifier.
          Can be None to indicate all params should be taken from kwargs.
      kwargs: {str:(str or func()->str)}, flags (available from context) or
          resolvers that can help parse this resource. If the fields in
          collection-path do not provide all the necessary information,
          kwargs will be searched for what remains.
    Returns:
      protorpc.messages.Message, The object containing info about this resource.

    Raises:
      InvalidCollectionException: If the provided collection-path is malformed.

    """
    parser = self._GetParserForCollection(collection)
    base_url = _GetApiBaseUrl(parser.collection_info.api_name,
                              parser.collection_info.api_version)

    parser_collection = parser.collection_info.full_name
    subcollection = ''
    if len(parser_collection) != len(collection):
      subcollection = collection[len(parser_collection)+1:]
    return parser.ParseResourceId(
        resource_id, kwargs, base_url, subcollection)

  def GetCollectionInfo(self, collection_name):
    api_name = _APINameFromCollection(collection_name)
    api_version = self.RegisterApiByName(api_name)
    parser = (self.parsers_by_collection
              .get(api_name, {}).get(api_version, {})
              .get(collection_name, None))
    return parser.collection_info

  def ParseURL(self, url):
    """Parse a URL into a Resource.

    This method does not yet handle "api.google.com" in place of
    "www.googleapis.com/api/version".

    Searches self.parsers_by_url to find a _ResourceParser. The parsers_by_url
    attribute is a deeply nested dictionary, where each key corresponds to
    a URL segment. The first segment is an API's base URL (eg.
    "https://www.googleapis.com/compute/v1/"), and after that it's each
    remaining token in the URL, split on '/'. Then a path down the tree is
    followed, keyed by the extracted pieces of the provided URL. If the key in
    the tree is a literal string, like "project" in .../project/{project}/...,
    the token from the URL must match exactly. If it's a parameter, like
    "{project}", then any token can match it, and that token is stored in a
    dict of params to with the associated key ("project" in this case). If there
    are no URL tokens left, and one of the keys at the current level is None,
    the None points to a _ResourceParser that can turn the collected
    params into a Resource.

    Args:
      url: str, The URL of the resource.

    Returns:
      Resource, The resource indicated by the provided URL.

    Raises:
      InvalidResourceException: If the provided URL could not be turned into
          a cloud resource.
    """
    match = _URL_RE.match(url)
    if not match:
      raise InvalidResourceException('unknown API host: [{0}]'.format(url))

    default_enpoint_url = core_apis.GetDefaultEndpointUrl(url)
    api_name, api_version, resource_path = (
        resource_util.SplitDefaultEndpointUrl(default_enpoint_url))
    if not url.startswith(default_enpoint_url):
      # Use last registered api version in case of override.
      api_version = self.registered_apis.get(api_name, [api_version])[-1]

    try:
      versions = core_apis.GetVersions(api_name)
    except core_apis.UnknownAPIError:
      raise InvalidResourceException(url)
    if api_version not in versions:
      raise InvalidResourceException(url)

    tokens = [api_name, api_version] + resource_path.split('/')
    endpoint = url[:-len(resource_path)]

    # Register relevant API if necessary and possible
    try:
      self.RegisterApiByName(api_name, api_version=api_version)
    except (core_apis.UnknownAPIError, core_apis.UnknownVersionError):
      # The caught InvalidResourceException has a less detailed message.
      raise InvalidResourceException(url)

    params = []
    cur_level = self.parsers_by_url
    for i, token in enumerate(tokens):
      if token in cur_level:
        # If the literal token is already here, follow it down.
        cur_level = cur_level[token]
      elif len(cur_level) == 1:
        # If the literal token is not here, and there is only one key, it must
        # be a parameter that will be added to the params dict.
        param, next_level = next(cur_level.iteritems())
        if param != '{}':
          raise InvalidResourceException(url)

        if len(next_level) == 1 and None in next_level:
          # This is the last parameter so we can combine the remaining tokens.
          token = '/'.join(tokens[i:])
          params.append(urllib.unquote(token))
          cur_level = next_level
          break

        # Clean up the provided value
        params.append(urllib.unquote(token))

        # Keep digging down.
        cur_level = next_level
      else:
        # If the token we want isn't here, and there isn't a single parameter,
        # the URL we've been given doesn't match anything we know about.
        raise InvalidResourceException(url)
      # Note: This will break if there are multiple parameters that could be
      # specified at a given level. As far as I can tell, this never happens and
      # never should happen. But in theory it's possible so we'll keep an eye
      # out for this issue.

      # No more tokens, so look for a parser.
    if None not in cur_level:
      raise InvalidResourceException(url)
    subcollection, parser = cur_level[None]
    params = dict(zip(parser.collection_info.GetParams(subcollection), params))
    return parser.ParseResourceId(
        None, params, base_url=endpoint,
        subcollection=subcollection)

  def ParseRelativeName(self, relative_name, collection, url_unescape=False):
    """Parser relative names. See Resource.RelativeName() method."""
    parser = self._GetParserForCollection(collection)
    base_url = _GetApiBaseUrl(parser.collection_info.api_name,
                              parser.collection_info.api_version)
    subcollection = parser.collection_info.GetSubcollection(collection)

    return parser.ParseRelativeName(
        relative_name, base_url, subcollection, url_unescape)

  def ParseStorageURL(self, url, collection=None):
    """Parse gs://bucket/object_path into storage.v1 api resource."""
    match = _GCS_URL_RE.match(url)
    if not match:
      raise InvalidResourceException('Invalid storage url: [{0}]'.format(url))
    if match.group(2):
      if collection and collection != 'storage.objects':
        raise WrongResourceCollectionException('storage.objects', collection,
                                               url)
      return self.ParseResourceId(
          collection='storage.objects',
          resource_id=None,
          kwargs={'bucket': match.group(1), 'object': match.group(2)})

    if collection and collection != 'storage.buckets':
      raise WrongResourceCollectionException('storage.buckets', collection, url)
    return self.ParseResourceId(
        collection='storage.buckets',
        resource_id=None,
        kwargs={'bucket': match.group(1)})

  def Parse(self, line, params=None, collection=None, enforce_collection=True):
    """Parse a Cloud resource from a command line.

    Args:
      line: str, The argument provided on the command line.
      params: {str:(str or func()->str)}, flags (available from context) or
        resolvers that can help parse this resource. If the fields in
        collection-path do not provide all the necessary information, params
        will be searched for what remains.
      collection: str, The resource's collection, or None if it should be
        inferred from the line.
      enforce_collection: bool, fail unless parsed resource is of this
        specified collection, this is applicable only if line is URL.

    Returns:
      A resource object.

    Raises:
      InvalidResourceException: If the line is invalid.
      UnknownFieldException: If resource is underspecified.
      UnknownCollectionException: If no collection is provided or can be
          inferred.
      WrongResourceCollectionException: If the provided URL points into a
          collection other than the one specified.
    """
    if line:
      if line.startswith('https://') or line.startswith('http://'):
        try:
          ref = self.ParseURL(line)
        except InvalidResourceException as e:
          # TODO(b/29573201): Make sure ParseURL handles this logic by default.
          bucket = None
          if line.startswith(_GCS_URL):
            try:
              bucket_prefix, bucket, object_prefix, objectpath = (
                  line[len(_GCS_URL):].split('/', 3))
            except ValueError:
              raise e
            if (bucket_prefix, object_prefix) != ('b', 'o'):
              raise
          elif line.startswith(_GCS_ALT_URL):
            line = line[len(_GCS_ALT_URL):]
            if '/' in line:
              bucket, objectpath = line.split('/', 1)
            else:
              return self.ParseResourceId(
                  collection='storage.buckets',
                  resource_id=None,
                  kwargs={'bucket': line})
          if bucket is not None:
            return self.ParseResourceId(
                collection='storage.objects',
                resource_id=None,
                kwargs={'bucket': bucket, 'object': objectpath})
          raise
        # TODO(user): consider not doing this here.
        # Validation of the argument is a distict concern.
        if (enforce_collection and collection and
            ref.Collection() != collection):
          raise WrongResourceCollectionException(
              expected=collection,
              got=ref.Collection(),
              path=ref.SelfLink())
        return ref
      elif line.startswith('gs://'):
        return self.ParseStorageURL(line, collection=collection)

    if line is not None and not line:
      raise InvalidResourceException(line)
    if not collection:
      raise UnknownCollectionException(line)

    return self.ParseResourceId(collection, line, params or {})

  def Create(self, collection, **params):
    """Create a Resource from known collection and params.

    Args:
      collection: str, The name of the collection the resource belongs to.
      **params: {str:str}, The values for each of the resource params.

    Returns:
      Resource, The constructed resource.
    """
    return self.Parse(None, collection=collection, params=params)

  def Clear(self):
    self.parsers_by_collection = {}
    self.parsers_by_url = {}
    self.default_param_funcs = {}
    self.registered_apis = collections.defaultdict(list)


# TODO(user): Deglobalize this object, force gcloud to manage it on its own.
REGISTRY = Registry()


def _GetApiBaseUrl(api_name, api_version):
  """Determine base url to use for resources of given version."""
  # Use current override endpoint for this resource name.
  endpoint_override_property = getattr(
      properties.VALUES.api_endpoint_overrides, api_name, None)
  base_url = None
  if endpoint_override_property is not None:
    base_url = endpoint_override_property.Get()
    if base_url is not None:
      # Check base url style. If it includes api version then override
      # also replaces the version, otherwise it only overrides the domain.
      client_class = core_apis.GetClientClass(api_name, api_version)
      _, url_version, _ = resource_util.SplitDefaultEndpointUrl(
          client_class.BASE_URL)
      if url_version is None:
        base_url += api_version + u'/'
  return base_url
