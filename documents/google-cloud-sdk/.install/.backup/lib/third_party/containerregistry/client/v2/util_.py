"""This package holds a handful of utilities for manipulating manifests."""



import base64
import hashlib
import json
import os
import subprocess

from containerregistry.client import docker_name  # pylint: disable=unused-import
from containerregistry.client import typing  # pylint: disable=unused-import

# TODO(user): Replace or remove.


class BadManifestException(Exception):
  """Exception type raised when a malformed manifest is encountered."""


def _JoseBase64UrlDecode(message):
  """Perform a JOSE-style base64 decoding of the supplied message.

  This is based on the docker/libtrust version of the similarly named
  function found here:
    https://github.com/docker/libtrust/blob/master/util.go

  Args:
    message: a JOSE-style base64 url-encoded message.
  Raises:
    BadManifestException: a malformed message was supplied.
  Returns:
    The decoded message.
  """
  l = len(message)
  if l % 4 == 0:
    pass
  elif l % 4 == 2:
    message += '=='
  elif l % 4 == 3:
    message += '='
  else:
    raise BadManifestException('Malformed JOSE Base64 encoding.')

  # Explicitly encode as ascii to work around issues passing unicode
  # to base64 decoding.
  return base64.urlsafe_b64decode(message.encode('ascii'))


def _ExtractProtectedRegion(
    signature
):
  """Extract the length and encoded suffix denoting the protected region."""
  protected = json.loads(_JoseBase64UrlDecode(signature['protected']))
  return (protected['formatLength'], protected['formatTail'])


def _ExtractCommonProtectedRegion(
    signatures
):
  """Verify that the signatures agree on the protected region and return one."""
  p = _ExtractProtectedRegion(signatures[0])
  for sig in signatures[1:]:
    if p != _ExtractProtectedRegion(sig):
      raise BadManifestException('Signatures disagree on protected region')
  return p


def DetachSignatures(
    manifest
):
  """Detach the signatures from the signed manifest and return the two halves.

  Args:
    manifest: a signed JSON manifest.
  Raises:
    BadManifestException: the provided manifest was improperly signed.
  Returns:
    a pair consisting of the manifest with the signature removed and a list of
    the removed signatures.
  """
  # First, decode the manifest to extract the list of signatures.
  json_manifest = json.loads(manifest)

  # Next, extract the signatures that have signed a portion of the manifest.
  signatures = json_manifest['signatures']

  # Do some basic validation of the signature input
  if len(signatures) < 1:
    raise BadManifestException('Expected a signed manifest.')
  for sig in signatures:
    if 'protected' not in sig:
      raise BadManifestException('Signature is missing "protected" key')

  # Establish the protected region and extract it from our original string.
  (format_length, format_tail) = _ExtractCommonProtectedRegion(signatures)
  suffix = _JoseBase64UrlDecode(format_tail)
  unsigned_manifest = manifest[0:format_length] + suffix

  return (unsigned_manifest, signatures)




def _AttachSignatures(
    manifest,
    signatures
):
  """Attach the provided signatures to the provided naked manifest."""
  (format_length, format_tail) = _ExtractCommonProtectedRegion(signatures)
  prefix = manifest[0:format_length]
  suffix = _JoseBase64UrlDecode(format_tail)
  return '{prefix},"signatures":{signatures}{suffix}'.format(
      prefix=prefix, signatures=json.dumps(signatures, sort_keys=True),
      suffix=suffix)


def Digest(manifest):
  """Compute the digest of the signed manifest."""
  unsigned_manifest, unused_signatures = DetachSignatures(manifest)
  return 'sha256:' + hashlib.sha256(unsigned_manifest).hexdigest()


def Rename(manifest, name):
  """Rename this signed manifest to the provided name, and resign it."""
  unsigned_manifest, unused_signatures = DetachSignatures(manifest)

  json_manifest = json.loads(unsigned_manifest)
  # Rewrite the name fields.
  json_manifest['name'] = name.repository
  json_manifest['tag'] = name.tag

  # Reserialize the json to a string.
  updated_unsigned_manifest = json.dumps(
      json_manifest, sort_keys=True, indent=2)

  # Sign the updated manifest
  return Sign(updated_unsigned_manifest)

