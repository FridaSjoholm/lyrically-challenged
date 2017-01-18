# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module that provides functions for handling rapt authentication."""

import base64
import getpass
import json
import sys
import urllib

from pyu2f import errors as u2ferrors
from pyu2f import model
from pyu2f import u2f


REAUTH_API = 'https://reauth.googleapis.com/v2/sessions'
REAUTH_SCOPE = 'https://www.googleapis.com/auth/accounts.reauth'
REAUTH_ORIGIN = 'https://accounts.google.com'


class ReauthError(Exception):
  """Base exception for reauthentication."""
  pass


class ReauthUnattendedError(ReauthError):
  """An exception for when reauth cannot be answered."""

  def __init__(self):
    super(ReauthUnattendedError, self).__init__(
        'Reauthentication challenge could not be answered because you are not '
        'in an interactive session.')


class ReauthFailError(ReauthError):
  """An exception for when reauth failed."""

  def __init__(self):
    super(ReauthFailError, self).__init__(
        'Reauthentication challenge failed.')


class ReauthAPIError(ReauthError):
  """An exception for when reauth API returned something we can't handle."""

  def __init__(self, api_error):
    super(ReauthAPIError, self).__init__(
        'Reauthentication challenge failed due to API error: {0}.'.format(
            api_error))


class ReauthAccessTokenRefreshError(ReauthError):
  """An exception for when we can't get an access token for reauth."""

  def __init__(self):
    super(ReauthAccessTokenRefreshError, self).__init__(
        'Failed to get an access token for reauthentication.')


def HandleErrors(msg):
  if 'error' in msg:
    raise ReauthAPIError(msg['error']['message'])
  return msg


class ReauthChallenge(object):
  """Base class for reauth challenges."""

  def __init__(self, http_request, access_token):
    self.http_request = http_request
    self.access_token = access_token

  def GetName(self):
    """Returns the name of the challenge. Must match what the server expects."""
    raise NotImplementedError()

  def IsLocallyEligible(self):
    """Returns true if a challenge is supported locally on this machine."""
    raise NotImplementedError()

  def Execute(self, metadata, session_id):
    """Execute internal challenge logic and pass credentials to reauth API."""
    client_input = self.InternalObtainCredentials(metadata)

    if not client_input:
      return None

    body = {
        'sessionId': session_id,
        'challengeId': metadata['challengeId'],
        'action': 'RESPOND',
        'proposalResponse': client_input,
    }
    _, content = self.http_request(
        '{0}/{1}:continue'.format(REAUTH_API, session_id),
        method='POST',
        body=json.dumps(body),
        headers={'Authorization': 'Bearer ' + self.access_token}
    )
    response = json.loads(content)
    HandleErrors(response)
    return response

  def InternalObtainCredentials(self, metadata):
    """Performs logic required to obtain credentials and returns it."""
    raise NotImplementedError()


class PasswordChallenge(ReauthChallenge):
  """Challenge that asks for user's password."""

  def GetName(self):
    return 'PASSWORD'

  def IsLocallyEligible(self):
    return True

  def InternalObtainCredentials(self, unused_metadata):
    passwd = getpass.getpass('Please enter your password:')
    if not passwd:
      passwd = ' '  # avoid the server crashing in case of no password :D
    return {'credential': passwd}


class SecurityKeyChallenge(ReauthChallenge):
  """Challenge that asks for user's security key touch."""

  def GetName(self):
    return 'SECURITY_KEY'

  def IsLocallyEligible(self):
    return True

  def InternalObtainCredentials(self, metadata):
    api = None
    try:
      api = u2f.GetLocalU2FInterface(origin=REAUTH_ORIGIN)
    except u2ferrors.NoDeviceFoundError:
      sys.stderr.write('Please insert your security key and press enter...')
      raw_input()
      try:
        api = u2f.GetLocalU2FInterface(origin=REAUTH_ORIGIN)
      except u2ferrors.NoDeviceFoundError:
        return None

    sk = metadata['securityKey']
    challenges = sk['challenges']
    app_id = sk['applicationId']

    sys.stderr.write('Please touch your security key.\n')
    for c in challenges:
      kh = c['keyHandle'].encode('ascii')
      key = model.RegisteredKey(bytearray(base64.urlsafe_b64decode(kh)))
      challenge = c['challenge'].encode('ascii')
      challenge = base64.urlsafe_b64decode(challenge)

      try:
        ret = api.Authenticate(app_id, challenge, [key])
        client_data = base64.urlsafe_b64encode(ret.client_data.GetJson())
        signature_data = base64.urlsafe_b64encode(ret.signature_data)
        payload = {
            'securityKey': {
                'clientData': client_data,
                'signatureData': signature_data,
                'applicationId': app_id,
                'keyHandle': c['keyHandle'],
            }
        }
        return payload
      except u2ferrors.U2FError as e:
        if e.code == u2ferrors.U2FError.DEVICE_INELIGIBLE:
          continue
        elif e.code == u2ferrors.U2FError.TIMEOUT:
          sys.stderr.write('Timed out while waiting for security key touch.\n')
          continue
        else:
          raise e
    return None


class ReauthManager(object):
  """Reauth manager class that handles reauth challenges."""

  def __init__(self, http_request, access_token):
    self.http_request = http_request
    self.access_token = access_token
    self.challenges = self.InternalBuildChallenges()

  def InternalBuildChallenges(self):
    out = {}
    for c in [SecurityKeyChallenge(self.http_request, self.access_token),
              PasswordChallenge(self.http_request, self.access_token)]:
      if c.IsLocallyEligible():
        out[c.GetName()] = c
    return out

  def InternalStart(self, requested_scopes):
    """Does initial request to reauth API and initialize the challenges."""
    body = {'supportedChallengeTypes': self.challenges.keys()}
    if requested_scopes:
      body['oauthScopesForDomainPolicyLookup'] = requested_scopes
    _, content = self.http_request(
        '{0}:start'.format(REAUTH_API),
        method='POST',
        body=json.dumps(body),
        headers={'Authorization': 'Bearer ' + self.access_token}
    )
    response = json.loads(content)
    HandleErrors(response)
    return response

  def DoOneRoundOfChallenges(self, msg):
    next_msg = None
    for challenge in msg['challenges']:
      if challenge['status'] != 'READY':
        # Skip non-activated challneges.
        continue
      c = self.challenges[challenge['challengeType']]
      next_msg = c.Execute(challenge, msg['sessionId'])
    return next_msg

  def ObtainProofOfReauth(self, requested_scopes=None):
    """Obtain proof of reauth (rapt token)."""
    msg = None
    max_challenge_count = 5

    while max_challenge_count:
      max_challenge_count -= 1

      if not msg:
        msg = self.InternalStart(requested_scopes)

      if msg['status'] == 'AUTHENTICATED':
        return msg['encodedProofOfReauthToken']

      if not (msg['status'] == 'CHALLENGE_REQUIRED' or
              msg['status'] == 'CHALLENGE_PENDING'):
        raise ReauthAPIError('Challenge status {0}'.format(msg['status']))

      if not sys.stdin.isatty():
        raise ReauthUnattendedError()

      msg = self.DoOneRoundOfChallenges(msg)

    # If we got here it means we didn't get authenticated.
    raise ReauthFailError()


def ObtainRapt(http_request, access_token, requested_scopes):
  rm = ReauthManager(http_request, access_token)
  rapt = rm.ObtainProofOfReauth(requested_scopes=requested_scopes)
  return rapt


def GetRaptToken(http_request, client_id, client_secret, refresh_token,
                 token_uri, scopes=None):
  """Given an http request method and refresh_token, get rapt token."""
  sys.stderr.write('Reauthentication required.\n')

  # Get access token for reauth.
  query_params = {
      'client_id': client_id,
      'client_secret': client_secret,
      'refresh_token': refresh_token,
      'scope': REAUTH_SCOPE,
      'grant_type': 'refresh_token',
  }
  _, content = http_request(
      token_uri,
      method='POST',
      body=urllib.urlencode(query_params),
      headers={'Content-Type': 'application/x-www-form-urlencoded'},
  )
  try:
    reauth_access_token = json.loads(content)['access_token']
  except (ValueError, KeyError) as _:
    raise ReauthAccessTokenRefreshError

  # Get rapt token from reauth API.
  rapt_token = ObtainRapt(
      http_request,
      reauth_access_token,
      requested_scopes=scopes)

  return rapt_token
