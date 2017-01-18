"""This package manages interaction sessions with the docker registry.

'Push' implements the go/docker:push session.
'Pull' is not implemented (go/docker:pull).
"""



import httplib
import logging

from containerregistry.client import docker_creds
from containerregistry.client import docker_name  # pylint: disable=unused-import
from containerregistry.client import typing  # pylint: disable=unused-import
from containerregistry.client.v1 import docker_http
from containerregistry.client.v1 import docker_image  # pylint: disable=unused-import

import httplib2  # pylint: disable=unused-import


class Push(object):
  """Push encapsulates a go/docker:push session."""

  def __init__(
      self,
      name,
      creds,
      transport):
    """Constructor.

    Args:
      name: the fully-qualified name of the tag to push.
      creds: provider for authorizing requests.
      transport: the http transport to use for sending requests.

    Raises:
      TypeError: an incorrectly typed argument was supplied.
    """
    self._name = name
    self._basic_creds = creds
    self._transport = transport
    self._top = None

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # This initiates the upload by issuing:
    #   PUT H:P/v1/repositories/R/
    # In that request, we specify the headers:
    #   Content-Type: application/json
    #   Authorization: Basic {base64 encoded auth token}
    #   X-Docker-Token: true
    resp, unused_content = docker_http.Request(
        self._transport,
        '{scheme}://{registry}/v1/repositories/{repository}/'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            repository=self._name.repository),
        self._basic_creds,
        accepted_codes=[httplib.OK, httplib.CREATED],
        body='[]')

    # The response should have an X-Docker-Token header, which
    # we should extract and annotate subsequent requests with:
    #   Authorization: Token {extracted value}
    self._token_creds = docker_creds.Token(resp['x-docker-token'])

    self._endpoint = resp['x-docker-endpoints']
    # TODO(user): Consider also supporting cookies, which are
    # used by Quay.io for authenticated sessions.

    logging.info('Initiated upload of: %s', self._name)
    return self

  def _exists(self, layer_id):
    """Check the remote for the given layer."""
    resp, unused_content = docker_http.Request(
        self._transport,
        '{scheme}://{endpoint}/v1/images/{layer}/json'.format(
            scheme=docker_http.Scheme(self._endpoint),
            endpoint=self._endpoint,
            layer=layer_id),
        self._token_creds,
        accepted_codes=[httplib.OK, httplib.NOT_FOUND])
    return resp.status == httplib.OK

  def _put_json(
      self,
      image,
      layer_id
  ):
    """Upload the json for a single layer."""
    docker_http.Request(self._transport,
                        '{scheme}://{endpoint}/v1/images/{layer}/json'.format(
                            scheme=docker_http.Scheme(self._endpoint),
                            endpoint=self._endpoint,
                            layer=layer_id),
                        self._token_creds,
                        accepted_codes=[httplib.OK],
                        body=image.json(layer_id))

  def _put_layer(
      self,
      image,
      layer_id
  ):
    """Upload the aufs tarball for a single layer."""
    # TODO(user): We should stream this instead of loading
    # it into memory.
    docker_http.Request(self._transport,
                        '{scheme}://{endpoint}/v1/images/{layer}/layer'.format(
                            scheme=docker_http.Scheme(self._endpoint),
                            endpoint=self._endpoint,
                            layer=layer_id),
                        self._token_creds,
                        accepted_codes=[httplib.OK],
                        body=image.layer(layer_id),
                        content_type='application/octet-stream')

  def _put_checksum(self, image,
                    layer_id):
    """Upload the checksum for a single layer."""
    # GCR doesn't use this for anything today,
    # so no point in implementing it.
    pass

  def _upload_one(
      self,
      image,
      layer_id
  ):
    """Upload a single layer, after checking whether it exists already."""
    if self._exists(layer_id):
      logging.info('Layer %s exists, skipping', layer_id)
      return

    # TODO(user): This ordering is consistent with the docker client,
    # however, only the json needs to be uploaded serially.  We can upload
    # the blobs in parallel.  Today, GCR allows the layer to be uploaded
    # first.
    self._put_json(image, layer_id)
    self._put_layer(image, layer_id)
    self._put_checksum(image, layer_id)
    logging.info('Layer %s pushed.', layer_id)

  def upload(self, image):
    """Upload the layers of the given image.

    Args:
      image: the image tarball to upload.
    """
    self._top = image.top()
    for layer in reversed(image.ancestry(self._top)):
      self._upload_one(image, layer)

  def _put_tag(self):
    """Upload the new value of the tag we are pushing."""
    docker_http.Request(
        self._transport,
        '{scheme}://{endpoint}/v1/repositories/{repository}/tags/{tag}'
        .format(scheme=docker_http.Scheme(self._endpoint),
                endpoint=self._endpoint,
                repository=self._name.repository,
                tag=self._name.tag),
        self._token_creds,
        accepted_codes=[httplib.OK],
        body='"%s"' % self._top)

  def _put_images(self):
    """Close the session by putting to the .../images endpoint."""
    docker_http.Request(
        self._transport,
        '{scheme}://{registry}/v1/repositories/{repository}/images'
        .format(scheme=docker_http.Scheme(self._name.registry),
                registry=self._name.registry,
                repository=self._name.repository),
        self._basic_creds,
        accepted_codes=[httplib.NO_CONTENT],
        body='[]')

  def __exit__(self, exception_type, unused_value, unused_traceback):
    if exception_type:
      logging.error('Error during upload of: %s', self._name)
      return

    # This should complete the upload by issuing:
    #   PUT server1/v1/repositories/R/tags/T
    # for each tag, with token auth talking to endpoint.
    self._put_tag()
    # Then issuing:
    #   PUT H:P/v1/repositories/R/images
    # to complete the transation, with basic auth talking to registry.
    self._put_images()

    logging.info('Finished upload of: %s', self._name)

