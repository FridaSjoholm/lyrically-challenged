# Copyright 2016 Google Inc. All Rights Reserved.
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

"""A command that prints an access token for Application Default Credentials.
"""

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from oauth2client import client


class PrintAccessToken(base.Command):
  """Print an access token for the your current Application Default Credentials.

  Once you have generated Application Default Credentials using
  `{parent_command} login`, you can use this command to generate and print
  an access token that can be directly used for making an API call. This can be
  useful for manually testing out APIs via curl.
  """

  @staticmethod
  def Args(parser):
    pass

  def Format(self, unused_args):
    return 'value(access_token)'

  def Run(self, args):
    """Run the helper command."""

    try:
      creds = client.GoogleCredentials.get_application_default()
    except client.ApplicationDefaultCredentialsError as e:
      log.debug(e, exc_info=True)
      raise c_exc.ToolException(str(e))

    if creds.create_scoped_required():
      creds_type = creds.serialization_data['type']
      token_uri_override = properties.VALUES.auth.token_host.Get()
      if creds_type == client.SERVICE_ACCOUNT and token_uri_override:
        creds = creds.create_scoped([auth_util.CLOUD_PLATFORM_SCOPE],
                                    token_uri=token_uri_override)
      else:
        creds = creds.create_scoped([auth_util.CLOUD_PLATFORM_SCOPE])

    access_token_info = creds.get_access_token()
    if not access_token_info:
      raise c_exc.ToolException(
          'No access token could be obtained from the current credentials.')

    return access_token_info
