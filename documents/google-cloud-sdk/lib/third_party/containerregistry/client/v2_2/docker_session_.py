"""This package manages pushes to and deletes from a v2 docker registry."""



import httplib
import logging
import urllib
import urlparse
import concurrent.futures

from containerregistry.client import docker_creds  # pylint: disable=unused-import
from containerregistry.client import docker_name
from containerregistry.client import typing  # pylint: disable=unused-import
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image  # pylint: disable=unused-import
from containerregistry.client.v2_2 import util
import httplib2  # pylint: disable=unused-import


def _tag_or_digest(
    name
):
  if isinstance(name, docker_name.Tag):
    return name.tag
  else:
    assert isinstance(name, docker_name.Digest)
    return name.digest


class Push(object):
  """Push encapsulates a Registry v2.2 Docker push session."""

  def __init__(
      self,
      name,
      creds,
      transport,
      mount=None,
      threads=1):
    """Constructor.

    If multiple threads are used, the caller *must* ensure that the provided
    transport is thread-safe, as well as the image that is being uploaded.
    It is notable that tarfile and httplib2.Http in Python are NOT threadsafe.

    Args:
      name: the fully-qualified name of the tag to push
      creds: credential provider for authorizing requests
      transport: the http transport to use for sending requests
      mount: list of repos from which to mount blobs.
      threads: the number of threads to use for uploads.

    Raises:
      ValueError: an incorrectly typed argument was supplied.
    """
    self._name = name
    self._transport = docker_http.Transport(
        name, creds, transport, docker_http.PUSH)
    self._mount = mount
    self._threads = threads

  def _base_url(self):
    return '{scheme}://{registry}/v2/{repository}'.format(
        scheme=docker_http.Scheme(self._name.registry),
        registry=self._name.registry,
        repository=self._name.repository)

  def _blob_exists(self, digest):
    """Check the remote for the given layer."""
    # HEAD the blob, and check for a 200
    resp, unused_content = self._transport.Request(
        '{base_url}/blobs/{digest}'.format(
            base_url=self._base_url(),
            digest=digest),
        method='HEAD', accepted_codes=[httplib.OK, httplib.NOT_FOUND])

    return resp.status == httplib.OK

  def _manifest_exists(self, image):
    """Check the remote for the given manifest by digest."""
    manifest_digest = util.Digest(image.manifest())

    # GET the manifest by digest, and check for 200
    resp, unused_content = self._transport.Request(
        '{base_url}/manifests/{digest}'.format(
            base_url=self._base_url(),
            digest=manifest_digest),
        method='GET', accepted_codes=[httplib.OK, httplib.NOT_FOUND])

    return resp.status == httplib.OK

  def _get_blob(
      self,
      image,
      digest
  ):
    if digest == image.config_blob():
      return image.config_file()
    return image.blob(digest)

  def _monolithic_upload(
      self,
      image,
      digest
  ):
    self._transport.Request(
        '{base_url}/blobs/uploads/?digest={digest}'.format(
            base_url=self._base_url(),
            digest=digest),
        method='POST', body=self._get_blob(image, digest),
        accepted_codes=[httplib.CREATED])

  def _add_digest(
      self,
      url,
      digest
  ):
    scheme, netloc, path, query_string, fragment = urlparse.urlsplit(url)
    qs = urlparse.parse_qs(query_string)
    qs['digest'] = [digest]
    query_string = urllib.urlencode(qs, doseq=True)
    return urlparse.urlunsplit(
        (scheme, netloc, path, query_string, fragment))

  def _put_upload(
      self,
      image,
      digest
  ):
    mounted, location = self._start_upload(digest, self._mount)

    if mounted:
      logging.info('Layer %s mounted.', digest)
      return

    location = self._add_digest(location, digest)
    self._transport.Request(
        location, method='PUT', body=self._get_blob(image, digest),
        accepted_codes=[httplib.CREATED])

  def _patch_upload(
      self,
      image,
      digest
  ):
    mounted, location = self._start_upload(digest, self._mount)

    if mounted:
      logging.info('Layer %s mounted.', digest)
      return

    resp, unused_content = self._transport.Request(
        location, method='PATCH', body=self._get_blob(image, digest),
        content_type='application/octet-stream',
        accepted_codes=[httplib.NO_CONTENT, httplib.ACCEPTED])

    location = self._add_digest(resp['location'], digest)
    self._transport.Request(
        location, method='PUT', body=None,
        accepted_codes=[httplib.CREATED])

  def _put_blob(
      self,
      image,
      digest
  ):
    """Upload the aufs .tgz for a single layer."""
    # We have a few choices for unchunked uploading:
    if not self._mount:
    #   POST to /v2/<name>/blobs/uploads/?digest=<digest>
    # TODO(user): Not supported by DockerHub
      self._monolithic_upload(image, digest)
    else:
    # or:
    #   POST /v2/<name>/blobs/uploads/        (no body*)
    #   PUT  /v2/<name>/blobs/uploads/<uuid>  (full body)
      self._put_upload(image, digest)
    # or:
    #   POST   /v2/<name>/blobs/uploads/        (no body*)
    #   PATCH  /v2/<name>/blobs/uploads/<uuid>  (full body)
    #   PUT    /v2/<name>/blobs/uploads/<uuid>  (no body)
    # self._patch_upload(image, digest)
    #
    # * We attempt to perform a cross-repo mount if any repositories are
    # specified in the "mount" parameter. This does a fast copy from a
    # repository that is known to contain this blob and skips the upload.

  def _remote_tag_digest(self):
    """Check the remote for the given manifest by digest."""

    # GET the tag we're pushing
    resp, unused_content = self._transport.Request(
        '{base_url}/manifests/{tag}'.format(
            base_url=self._base_url(),
            tag=self._name.tag),
        method='GET', accepted_codes=[httplib.OK, httplib.NOT_FOUND])

    if resp.status == httplib.NOT_FOUND:
      return None

    return resp['docker-content-digest']

  def _put_manifest(self, image):
    """Upload the manifest for this image."""
    self._transport.Request(
        '{base_url}/manifests/{tag_or_digest}'.format(
            base_url=self._base_url(),
            tag_or_digest=_tag_or_digest(self._name)),
        method='PUT', body=image.manifest(),
        content_type=docker_http.MANIFEST_SCHEMA2_MIME,
        accepted_codes=[httplib.OK, httplib.ACCEPTED])

  def _start_upload(
      self,
      digest,
      mount=None
  ):
    """POST to begin the upload process with optional cross-repo mount param."""
    if not mount:
      # Do a normal POST to initiate an upload if mount is missing.
      url = '{base_url}/blobs/uploads/'.format(base_url=self._base_url())
      accepted_codes = [httplib.ACCEPTED]
    else:
      # If we have a mount parameter, try to mount the blob from another repo.
      mount_from = '&'.join(
          ['from=' + urllib.quote(repo.repository, '') for repo in self._mount])
      url = '{base_url}/blobs/uploads/?mount={digest}&{mount_from}'.format(
          base_url=self._base_url(),
          digest=digest,
          mount_from=mount_from)
      accepted_codes = [httplib.CREATED, httplib.ACCEPTED]

    resp, unused_content = self._transport.Request(
        url, method='POST', body=None,
        accepted_codes=accepted_codes)
    return (resp.status == httplib.CREATED, resp.get('location'))

  def _upload_one(
      self,
      image,
      digest
  ):
    """Upload a single layer, after checking whether it exists already."""
    if self._blob_exists(digest):
      logging.info('Layer %s exists, skipping', digest)
      return

    self._put_blob(image, digest)
    logging.info('Layer %s pushed.', digest)

  def upload(self, image):
    """Upload the layers of the given image.

    Args:
      image: the image to upload.
    """
    # If the manifest (by digest) exists, then avoid N layer existence
    # checks (they must exist).
    if self._manifest_exists(image):
      if isinstance(self._name, docker_name.Tag):
        manifest_digest = util.Digest(image.manifest())
        if self._remote_tag_digest() == manifest_digest:
          logging.info('Tag points to the right manifest, skipping push.')
          return
        logging.info('Manifest exists, skipping blob uploads and pushing tag.')
      else:
        logging.info('Manifest exists, skipping upload.')
    elif self._threads == 1:
      for digest in image.blob_set():
        self._upload_one(image, digest)
    else:
      with concurrent.futures.ThreadPoolExecutor(
          max_workers=self._threads) as executor:
        future_to_params = {
            executor.submit(self._upload_one, image, digest): (image, digest)
            for digest in image.blob_set()}
        for future in concurrent.futures.as_completed(future_to_params):
          future.result()

    # This should complete the upload by uploading the manifest.
    self._put_manifest(image)

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, exception_type, unused_value, unused_traceback):
    if exception_type:
      logging.error('Error during upload of: %s', self._name)
      return
    logging.info('Finished upload of: %s', self._name)


def Delete(
    name,
    creds,
    transport
):
  """Delete a tag or digest.

  Args:
    name: a tag or digest to be deleted.
    creds: the creds to use for deletion.
    transport: the transport to use to contact the registry.
  """
  docker_transport = docker_http.Transport(
      name, creds, transport, docker_http.DELETE)

  resp, unused_content = docker_transport.Request(
      '{scheme}://{registry}/v2/{repository}/manifests/{entity}'.format(
          scheme=docker_http.Scheme(name.registry),
          registry=name.registry,
          repository=name.repository,
          entity=_tag_or_digest(name)),
      method='DELETE',
      accepted_codes=[httplib.OK])

