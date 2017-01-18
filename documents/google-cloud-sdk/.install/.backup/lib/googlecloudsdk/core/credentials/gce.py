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

"""Fetching GCE metadata."""

import mutex
import urllib2

from googlecloudsdk.core.credentials import gce_cache
from googlecloudsdk.core.credentials import gce_read
from googlecloudsdk.core.util import retry


class Error(Exception):
  """Exceptions for the gce module."""


class MetadataServerException(Error):
  """Exception for when the metadata server cannot be reached."""


class CannotConnectToMetadataServerException(MetadataServerException):
  """Exception for when the metadata server cannot be reached."""


@retry.RetryOnException(max_retrials=3)
def _ReadNoProxyWithCleanFailures(uri, http_errors_to_ignore=()):
  """Reads data from a URI with no proxy, yielding cloud-sdk exceptions."""
  try:
    return gce_read.ReadNoProxy(uri)
  except urllib2.HTTPError as e:
    if e.code in http_errors_to_ignore:
      return None
    raise MetadataServerException(e)
  except urllib2.URLError as e:
    raise CannotConnectToMetadataServerException(e)


class _GCEMetadata(object):
  """Class for fetching GCE metadata.

  Attributes:
      connected: bool, True if the metadata server is available.

  """

  def __init__(self):
    self.connected = gce_cache.GetOnGCE()

  def DefaultAccount(self):
    """Get the default service account for the host GCE instance.

    Fetches GOOGLE_GCE_METADATA_DEFAULT_ACCOUNT_URI and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The email address for the default service account. None if not on a
          GCE VM, or if there are no service accounts associated with this VM.
    """

    if not self.connected:
      return None

    return _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_DEFAULT_ACCOUNT_URI,
        http_errors_to_ignore=(404,))

  def Project(self):
    """Get the project that owns the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_PROJECT_URI and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The email address for the default service account. None if not on a
          GCE VM.
    """

    if not self.connected:
      return None

    return _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_PROJECT_URI)

  def Accounts(self):
    """Get the list of service accounts available from the metadata server.

    Returns:
      [str], The list of accounts. [] if not on a GCE VM.

    Raises:
      CannotConnectToMetadataServerException: If no metadata server is present.
      MetadataServerException: If there is a problem communicating with the
          metadata server.
    """

    if not self.connected:
      return []

    accounts_listing = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_ACCOUNTS_URI + '/')
    accounts_lines = accounts_listing.split()
    accounts = []
    for account_line in accounts_lines:
      account = account_line.strip('/')
      if account == 'default':
        continue
      accounts.append(account)
    return accounts

  def Zone(self):
    """Get the name of the zone containing the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_ZONE_URI, formats it, and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The short name (e.g., us-central1-f) of the zone containing the
          current instance.
      None if not on a GCE VM.
    """

    if not self.connected:
      return None

    # zone_path will be formatted as, for example,
    # projects/123456789123/zones/us-central1-f
    # and we want to return only the last component.
    zone_path = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_ZONE_URI)
    return zone_path.split('/')[-1]

  def Region(self):
    """Get the name of the region containing the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_ZONE_URI, extracts the region associated
    with the zone, and returns it.  Extraction is based property that
    zone names have form <region>-<zone> (see https://cloud.google.com/
    compute/docs/zones) and an assumption that <zone> contains no hyphens.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The short name (e.g., us-central1) of the region containing the
          current instance.
      None if not on a GCE VM.
    """

    if not self.connected:
      return None

    # Zone will be formatted as (e.g.) us-central1-a, and we want to return
    # everything ahead of the last hyphen.
    zone = self.Zone()
    return '-'.join(zone.split('-')[:-1])


_metadata = None
_metadata_lock = mutex.mutex()


def Metadata():
  """Get a singleton for the GCE metadata class.

  Returns:
    _GCEMetadata, An object used to collect information from the GCE metadata
    server.
  """
  def _CreateMetadata(unused_none):
    global _metadata
    if not _metadata:
      _metadata = _GCEMetadata()
  _metadata_lock.lock(function=_CreateMetadata, argument=None)
  _metadata_lock.unlock()
  return _metadata
