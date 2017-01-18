# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for adding a path matcher to a URL map."""

import collections
import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_buckets import (
    flags as backend_bucket_flags)
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.url_maps import flags


def _Args(parser):
  """Common arguments to add-path-matcher commands for each release track."""
  parser.add_argument(
      '--description',
      help='An optional, textual description for the path matcher.')

  parser.add_argument(
      '--path-matcher-name',
      required=True,
      help='The name to assign to the path matcher.')

  parser.add_argument(
      '--path-rules',
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      metavar='PATH=SERVICE',
      help='Rules for mapping request paths to services.')

  host_rule = parser.add_mutually_exclusive_group()
  host_rule.add_argument(
      '--new-hosts',
      type=arg_parsers.ArgList(min_length=1),
      metavar='NEW_HOST',
      help=('If specified, a new host rule with the given hosts is created '
            'and the path matcher is tied to the new host rule.'))

  existing_host = host_rule.add_argument(
      '--existing-host',
      help='An existing host rule to tie the new path matcher to.')
  existing_host.detailed_help = """\
      An existing host rule to tie the new path matcher to. Although
      host rules can contain more than one host, only a single host
      is needed to uniquely identify the host rule.
      """

  parser.add_argument(
      '--delete-orphaned-path-matcher',
      action='store_true',
      default=False,
      help=('If provided and a path matcher is orphaned as a result of this '
            'command, the command removes the orphaned path matcher instead '
            'of failing.'))


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class AddPathMatcherGA(base_classes.ReadWriteCommand):
  """Add a path matcher to a URL map."""

  BACKEND_SERVICE_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMapPathMatcher())
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    _Args(parser)

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def resource_type(self):
    return 'urlMaps'

  def CreateReference(self, args):
    return self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

  def GetGetRequest(self, args):
    """Returns the request for the existing URL map resource."""
    return (self.service,
            'Get',
            self.messages.ComputeUrlMapsGetRequest(
                urlMap=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeUrlMapsUpdateRequest(
                urlMap=self.ref.Name(),
                urlMapResource=replacement,
                project=self.project))

  def _ModifyBase(self, args, existing):
    """Modifications to the URL map that are shared between release tracks.

    Args:
      args: the argparse arguments that this command was invoked with.
      existing: the existing URL map message.

    Returns:
      A modified URL map message.
    """
    replacement = copy.deepcopy(existing)

    if not args.new_hosts and not args.existing_host:
      new_hosts = ['*']
    else:
      new_hosts = args.new_hosts

    # If --new-hosts is given, we check to make sure none of those
    # hosts already exist and once the check succeeds, we create the
    # new host rule.
    if new_hosts:
      new_hosts = set(new_hosts)
      for host_rule in existing.hostRules:
        for host in host_rule.hosts:
          if host in new_hosts:
            raise exceptions.ToolException(
                'Cannot create a new host rule with host [{0}] because the '
                'host is already part of a host rule that references the path '
                'matcher [{1}].'.format(host, host_rule.pathMatcher))

      replacement.hostRules.append(self.messages.HostRule(
          hosts=sorted(new_hosts),
          pathMatcher=args.path_matcher_name))

    # If --existing-host is given, we check to make sure that the
    # corresponding host rule will not render a patch matcher
    # orphan. If the check succeeds, we change the path matcher of the
    # host rule. If the check fails, we remove the path matcher if
    # --delete-orphaned-path-matcher is given otherwise we fail.
    else:
      target_host_rule = None
      for host_rule in existing.hostRules:
        for host in host_rule.hosts:
          if host == args.existing_host:
            target_host_rule = host_rule
            break
        if target_host_rule:
          break

      if not target_host_rule:
        raise exceptions.ToolException(
            'No host rule with host [{0}] exists. Check your spelling or '
            'use [--new-hosts] to create a new host rule.'
            .format(args.existing_host))

      path_matcher_orphaned = True
      for host_rule in replacement.hostRules:
        if host_rule == target_host_rule:
          host_rule.pathMatcher = args.path_matcher_name
          continue

        if host_rule.pathMatcher == target_host_rule.pathMatcher:
          path_matcher_orphaned = False
          break

      if path_matcher_orphaned:
        # A path matcher will be orphaned, so now we determine whether
        # we should delete the path matcher or report an error.
        if args.delete_orphaned_path_matcher:
          replacement.pathMatchers = [
              path_matcher for path_matcher in existing.pathMatchers
              if path_matcher.name != target_host_rule.pathMatcher]
        else:
          raise exceptions.ToolException(
              'This operation will orphan the path matcher [{0}]. To '
              'delete the orphan path matcher, rerun this command with '
              '[--delete-orphaned-path-matcher] or use [gcloud compute '
              'url-maps edit] to modify the URL map by hand.'.format(
                  host_rule.pathMatcher))

    return replacement

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = self._ModifyBase(args, existing)

    # Creates PathRule objects from --path-rules.
    service_map = collections.defaultdict(set)
    for path, service in args.path_rules.iteritems():
      service_map[service].add(path)
    path_rules = []
    for service, paths in sorted(service_map.iteritems()):
      path_rules.append(
          self.messages.PathRule(
              paths=sorted(paths),
              service=self.resources.Parse(
                  service, collection='compute.backendServices').SelfLink()))

    new_path_matcher = self.messages.PathMatcher(
        defaultService=self.BACKEND_SERVICE_ARG.ResolveAsResource(
            args, self.resources).SelfLink(),
        description=args.description,
        name=args.path_matcher_name,
        pathRules=path_rules)

    replacement.pathMatchers.append(new_path_matcher)
    return replacement


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddPathMatcherAlpha(AddPathMatcherGA):
  """Add a path matcher to a URL map."""

  BACKEND_BUCKET_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_BUCKET_ARG = (
        backend_bucket_flags.BackendBucketArgumentForUrlMap())
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap())
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--default-service',
        help=('A backend service that will be used for requests that the path '
              'matcher cannot match. Exactly one of --default-service or '
              '--default-backend-bucket is required.'))
    group.add_argument(
        '--default-backend-bucket',
        help=('A backend bucket that will be used for requests that the path '
              'matcher cannot match. Exactly one of --default-service or '
              '--default-backend-bucket is required.'))

    parser.add_argument('--backend-service-path-rules',
                        type=arg_parsers.ArgDict(min_length=1),
                        default={},
                        metavar='PATH=SERVICE',
                        help='Rules for mapping request paths to services.')
    parser.add_argument(
        '--backend-bucket-path-rules',
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        metavar='PATH=BUCKET',
        help='Rules for mapping request paths to backend buckets.')

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = self._ModifyBase(args, existing)

    # Creates PathRule objects from --path-rules, --backend-service-path-rules,
    # and --backend-bucket-path-rules.
    service_map = collections.defaultdict(set)
    bucket_map = collections.defaultdict(set)
    for path, service in args.path_rules.iteritems():
      service_map[service].add(path)
    for path, service in args.backend_service_path_rules.iteritems():
      service_map[service].add(path)
    for path, bucket in args.backend_bucket_path_rules.iteritems():
      bucket_map[bucket].add(path)
    path_rules = []
    for service, paths in sorted(service_map.iteritems()):
      path_rules.append(
          self.messages.PathRule(
              paths=sorted(paths),
              service=self.resources.Parse(
                  service, collection='compute.backendServices').SelfLink()))
    for bucket, paths in sorted(bucket_map.iteritems()):
      path_rules.append(
          self.messages.PathRule(
              paths=sorted(paths),
              service=self.resources.Parse(
                  bucket, collection='compute.backendBuckets').SelfLink()))

    if args.default_service:
      default_backend_uri = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, self.resources).SelfLink()
    else:
      default_backend_uri = self.BACKEND_BUCKET_ARG.ResolveAsResource(
          args, self.resources).SelfLink()

    new_path_matcher = self.messages.PathMatcher(
        defaultService=default_backend_uri,
        description=args.description,
        name=args.path_matcher_name,
        pathRules=path_rules)

    replacement.pathMatchers.append(new_path_matcher)
    return replacement


AddPathMatcherGA.detailed_help = {
    'brief': 'Add a path matcher to a URL map',
    'DESCRIPTION': """\
        *{command}* is used to add a path matcher to a URL map. A path
        matcher maps HTTP request paths to backend services. Each path
        matcher must be referenced by at least one host rule. This
        command can create a new host rule through the ``--new-hosts''
        flag or it can reconfigure an existing host rule to point to
        the newly added path matcher using ``--existing-host''. In the
        latter case, if a path matcher is orphaned as a result of the
        operation, this command will fail unless
        ``--delete-orphaned-path-matcher'' is provided.
        """,
    'EXAMPLES': """\
        To create a rule for mapping the path ```/search/*``` to the
        hypothetical ```search-service``` and ```/images/*``` to the
        ```images-service``` under the hosts ```google.com``` and
        ```*.google.com```, run:

          $ {command} MY-URL-MAP --path-matcher-name MY-MATCHER --default-service MY-DEFAULT-SERVICE --path-rules '/search/*=search_service,/images/*=images-service' --new-hosts 'google.com,*.google.com'

        Note that a default service must be provided to handle paths
        for which there is no mapping.
        """,
}
AddPathMatcherAlpha.detailed_help = {
    'brief': 'Add a path matcher to a URL map',
    'DESCRIPTION': """\
        *{command}* is used to add a path matcher to a URL map. A path
        matcher maps HTTP request paths to backend services or backend
        buckets. Each path matcher must be referenced by at least one
        host rule. This command can create a new host rule through the
        ``--new-hosts'' flag or it can reconfigure an existing host rule
        to point to the newly added path matcher using ``--existing-host''.
        In the latter case, if a path matcher is orphaned as a result
        of the operation, this command will fail unless
        ``--delete-orphaned-path-matcher'' is provided.
        """,
    'EXAMPLES': """\
        To create a rule for mapping the path ```/search/*``` to the
        hypothetical ```search-service```, ```/static/*``` to the
        ```static-bucket``` backend bucket and ```/images/*``` to the
        ```images-service``` under the hosts ```google.com``` and
        ```*.google.com```, run:

          $ {command} MY-URL-MAP --path-matcher-name MY-MATCHER --default-service MY-DEFAULT-SERVICE --backend-service-path-rules '/search/*=search_service,/images/*=images-service' --backend-bucket-path-rules '/static/*=static-bucket' --new-hosts google.com '*.google.com'

        Note that a default service or default backend bucket must be
        provided to handle paths for which there is no mapping.
        """,
}
