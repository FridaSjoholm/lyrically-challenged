"""This package provides DockerImage for examining docker_build outputs."""



import abc
import cStringIO
import httplib
import json
import os
import tarfile

from containerregistry.client import docker_creds  # pylint: disable=unused-import
from containerregistry.client import docker_name
from containerregistry.client import typing  # pylint: disable=unused-import
from containerregistry.client.v2_2 import docker_http
import httplib2  # pylint: disable=unused-import


class DockerImage(object):
  """Interface for implementations that interact with Docker images."""

  __metaclass__ = abc.ABCMeta  # For enforcing that methods are overriden.

  def fs_layers(self):
    """The ordered collection of filesystem layers that comprise this image."""
    manifest = json.loads(self.manifest())
    return [x['digest'] for x in reversed(manifest['layers'])]

  def config_blob(self):
    manifest = json.loads(self.manifest())
    return manifest['config']['digest']

  def blob_set(self):
    """The unique set of blobs that compose to create the filesystem."""
    return set(self.fs_layers() + [self.config_blob()])

  @abc.abstractmethod
  def manifest(self):
    """The JSON manifest referenced by the tag/digest.

    Returns:
      The raw json manifest
    """

  @abc.abstractmethod
  def config_file(self):
    """The raw blob string of the config file."""

  def blob_size(self, digest):
    """The byte size of the raw blob."""
    return len(self.blob(digest))

  @abc.abstractmethod
  def blob(self, digest):
    """The raw blob of the layer.

    Args:
      digest: the 'algo:digest' of the layer being addressed.

    Returns:
      The raw blob string of the layer.
    """

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Open the image for reading."""

  @abc.abstractmethod
  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Close the image."""


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(
      self,
      name,
      basic_creds,
      transport):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._response = {}

  def _content(
      self,
      suffix,
      accepted_mimes=None,
      cache=True
  ):
    """Fetches content of the resources from registry by http calls."""
    if isinstance(self._name, docker_name.Repository):
      suffix = '{repository}/{suffix}'.format(
          repository=self._name.repository,
          suffix=suffix)

    if suffix in self._response:
      return self._response[suffix]

    _, content = self._transport.Request(
        '{scheme}://{registry}/v2/{suffix}'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            suffix=suffix),
        accepted_codes=[httplib.OK],
        accepted_mimes=accepted_mimes)
    if cache:
      self._response[suffix] = content
    return content

  def _tags(self):
    # See //cloud/containers/registry/proto/v2/tags.proto
    # for the full response structure.
    return json.loads(self._content('tags/list'))

  def tags(self):
    return self._tags().get('tags', [])

  def manifests(self):
    payload = self._tags()
    if 'manifest' not in payload:
      # Only GCR supports this schema.
      return {}
    return payload['manifest']

  def children(self):
    payload = self._tags()
    if 'child' not in payload:
      # Only GCR supports this schema.
      return []
    return payload['child']

  def exists(self):
    try:
      manifest = json.loads(self.manifest())
      return manifest['schemaVersion'] == 2
    except docker_http.V2DiagnosticException:
      # TODO(user): Check for 404
      return False

  def manifest(self):
    """Override."""
    # GET server1/v2/<name>/manifests/<tag_or_digest>
    accepted_mimes = docker_http.MANIFEST_SCHEMA2_MIMES

    if isinstance(self._name, docker_name.Tag):
      return self._content('manifests/' + self._name.tag, accepted_mimes)
    else:
      assert isinstance(self._name, docker_name.Digest)
      return self._content('manifests/' + self._name.digest, accepted_mimes)

  def config_file(self):
    """Override."""
    return self.blob(self.config_blob())

  def blob_size(self, digest):
    """The byte size of the raw blob."""
    suffix = 'blobs/' + digest
    if isinstance(self._name, docker_name.Repository):
      suffix = '{repository}/{suffix}'.format(
          repository=self._name.repository,
          suffix=suffix)

    resp, unused_content = self._transport.Request(
        '{scheme}://{registry}/v2/{suffix}'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            suffix=suffix),
        method='HEAD',
        accepted_codes=[httplib.OK])

    return int(resp['content-length'])

  # Large, do not memoize.
  def blob(self, digest):
    """Override."""
    # GET server1/v2/<name>/blobs/<digest>
    return self._content('blobs/' + digest, cache=False)

  def catalog(self, page_size=100):
    # TODO(user): Handle docker_name.Repository for /v2/<name>/_catalog
    if isinstance(self._name, docker_name.Repository):
      raise ValueError('Expected docker_name.Registry for "name"')

    url = '{scheme}://{registry}/v2/_catalog?n={page_size}'.format(
        scheme=docker_http.Scheme(self._name.registry),
        registry=self._name.registry,
        page_size=page_size)

    for _, content in self._transport.PaginatedRequest(
        url, accepted_codes=[httplib.OK]):
      wrapper_object = json.loads(content)

      if 'repositories' not in wrapper_object:
        raise docker_http.BadStateException(
            'Malformed JSON response: %s' % content)

      # TODO(user): This should return docker_name.Repository
      for repo in wrapper_object['repositories']:
        yield repo

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # Create a v2 transport to use for making authenticated requests.
    self._transport = docker_http.Transport(
        self._name, self._creds, self._original_transport, docker_http.PULL)

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


def _in_whiteout_dir(
    fs,
    name
):
  while name:
    dirname = os.path.dirname(name)
    if name == dirname:
      break
    if fs.get(dirname):
      return True
    name = dirname
  return False

_WHITEOUT_PREFIX = '.wh.'


def extract(image, tar):
  """Extract the final filesystem from the image into tar.

  Args:
    image: a docker image whose final filesystem to construct.
    tar: the tarfile into which we are writing the final filesystem.
  """
  # Maps all of the files we have already added (and should never add again)
  # to whether they are a tombstone or not.
  fs = {}

  # Walk the layers, topmost first and add files.  If we've seen them in a
  # higher layer then we skip them.
  for layer in image.fs_layers():
    buf = cStringIO.StringIO(image.blob(layer))
    with tarfile.open(mode='r:gz', fileobj=buf) as layer_tar:
      for member in layer_tar.getmembers():
        # If we see a whiteout file, then don't add anything to the tarball
        # but ensure that any lower layers don't add a file with the whited
        # out name.
        basename = os.path.basename(member.name)
        dirname = os.path.dirname(member.name)
        tombstone = basename.startswith(_WHITEOUT_PREFIX)
        if tombstone:
          basename = basename[len(_WHITEOUT_PREFIX):]

        # Before adding a file, check to see whether it (or its whiteout) have
        # been seen before.
        name = os.path.normpath(os.path.join('.', dirname, basename))
        if name in fs:
          continue

        # Check for a whited out parent directory
        if _in_whiteout_dir(fs, name):
          continue

        # Mark this file as handled by adding its name.
        # A non-directory implicitly tombstones any entries with
        # a matching (or child) name.
        fs[name] = tombstone or not member.isdir()
        if not tombstone:
          if member.isfile():
            tar.addfile(member, fileobj=layer_tar.extractfile(member.name))
          else:
            tar.addfile(member, fileobj=None)

