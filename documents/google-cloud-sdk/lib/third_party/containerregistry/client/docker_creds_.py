"""This package exposes credentials for talking to a Docker registry."""



import abc
import base64

from containerregistry.client import typing  # pylint: disable=unused-import
import httplib2  # pylint: disable=unused-import
from oauth2client import client as oauth2client  # pylint: disable=unused-import


class Provider(object):
  """Interface for providing User Credentials for use with a Docker Registry."""

  __metaclass__ = abc.ABCMeta  # For enforcing that methods are overriden.

  @abc.abstractmethod
  def Get(self):
    """Produces a value suitable for use in the Authorization header."""


class Anonymous(Provider):
  """Implementation for anonymous access."""

  def Get(self):
    """Implement anonymous authentication."""
    return ''


class _SchemeProvider(Provider):
  """Implementation for providing a challenge response credential."""

  def __init__(self, scheme):
    self._scheme = scheme

  @property
  @abc.abstractmethod
  def suffix(self):
    """Returns the authentication payload to follow the auth scheme."""

  def Get(self):
    """Gets the credential in a form suitable for an Authorization header."""
    return '%s %s' % (self._scheme, self.suffix)


# TODO(user): Move to v1
class Token(_SchemeProvider):
  """Implementation for providing a transaction's X-Docker-Token as creds."""

  def __init__(self, token):
    super(Token, self).__init__('Token')
    self._token = token

  @property
  def suffix(self):
    return self._token


# TODO(user): Move to v2
class Bearer(_SchemeProvider):
  """Implementation for providing a transaction's Bearer token as creds."""

  def __init__(self, bearer_token):
    super(Bearer, self).__init__('Bearer')
    self._bearer_token = bearer_token

  @property
  def suffix(self):
    return self._bearer_token


class Basic(_SchemeProvider):
  """Implementation for providing a username/password-based creds."""

  def __init__(self, username, password):
    super(Basic, self).__init__('Basic')
    self._username = username
    self._password = password

  @property
  def username(self):
    return self._username

  @property
  def password(self):
    return self._password

  @property
  def suffix(self):
    return base64.b64encode(self.username + ':' + self.password)

_USERNAME = '_token'


class OAuth2(Basic):
  """Base class for turning OAuth2Credentials into suitable GCR credentials."""

  def __init__(
      self,
      creds,
      transport):
    """Constructor.

    Args:
      creds: the credentials from which to retrieve access tokens.
      transport: the http transport to use for token exchanges.
    """
    super(OAuth2, self).__init__(_USERNAME, 'does not matter')
    self._creds = creds
    self._transport = transport

  @property
  def password(self):
    # WORKAROUND...
    # The python oauth2client library only loads the credential from an
    # on-disk cache the first time 'refresh()' is called, and doesn't
    # actually 'Force a refresh of access_token' as advertised.
    # This call will load the credential, and the call below will refresh
    # it as needed.  If the credential is unexpired, the call below will
    # simply return a cache of this refresh.
    unused_at = self._creds.get_access_token(http=self._transport)

    # Most useful API ever:
    # https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={at}
    return self._creds.get_access_token(http=self._transport).access_token

