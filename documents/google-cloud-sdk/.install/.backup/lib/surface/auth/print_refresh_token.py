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

"""A hidden command that prints access tokens.
"""

from googlecloudsdk.api_lib.auth import refresh_token
from googlecloudsdk.calliope import base


@base.Hidden
class PrintRefreshToken(base.Command):
  """A command that prints the access token for the current account."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'account', nargs='?',
        help=('The account to get the access token for. Leave empty for the '
              'active account.'))

  def Run(self, args):
    """Run the helper command."""

    return {
        'refresh_token': refresh_token.GetForAccount(args.account)
    }

  def Format(self, args):
    return 'value(refresh_token)'

