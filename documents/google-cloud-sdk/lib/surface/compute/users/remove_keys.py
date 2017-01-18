# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for removing public keys to users."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.users import client as users_client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.users import utils as user_utils
from googlecloudsdk.command_lib.util import gaia


class RemoveKeys(base_classes.NoOutputAsyncMutator):
  """Remove a public key from a Google Compute Engine user.

  *{command}* removes public keys from a Google Compute Engine user.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--fingerprints',
        type=arg_parsers.ArgList(min_length=1),
        metavar='FINGERPRINT',
        help='The fingerprints of the public keys to remove from the user.')

    user_utils.AddUserArgument(parser, '', custom_help=(
        'If provided, the name of the user to remove public keys from. '
        'Else, the default user will be used.'))

  @property
  def service(self):
    return self.clouduseraccounts.users

  @property
  def method(self):
    return 'RemovePublicKey'

  @property
  def resource_type(self):
    return 'users'

  @property
  def messages(self):
    return self.clouduseraccounts.MESSAGES_MODULE

  def CreateRequests(self, args):

    name = args.name
    if not name:
      name = gaia.GetDefaultAccountName(self.http)

    user_ref = self.clouduseraccounts_resources.Parse(
        name, collection='clouduseraccounts.users')

    if args.fingerprints:
      fingerprints = args.fingerprints
    else:
      fetcher = users_client.UserResourceFetcher(
          self.clouduseraccounts, self.project, self.http, self.batch_url)

      fingerprints = [k.fingerprint for k in
                      fetcher.LookupUser(user_ref.Name()).publicKeys]

    # Generate warning before deleting.
    prompt_list = ['[{0}]'.format(fingerprint) for fingerprint in fingerprints]
    prompt_title = ('The following public keys will be removed from the user ' +
                    user_ref.Name())
    utils.PromptForDeletionHelper(None, prompt_list, prompt_title=prompt_title)

    requests = []
    for fingerprint in fingerprints:
      request = self.messages.ClouduseraccountsUsersRemovePublicKeyRequest(
          project=self.project,
          fingerprint=fingerprint,
          user=user_ref.Name())
      requests.append(request)

    return requests


RemoveKeys.detailed_help = {
    'EXAMPLES': """\
        To remove all public keys for a user, run:

          $ {command} example-user

        To remove a specific public key, first describe the user
        (using `gcloud compute users describe example-user`) to determine the
        fingerprints of the public keys you wish
        to remove. Then run:

          $ {command} example-user --fingerprints b3ca856958b524f3f12c3e43f6c9065d
        """,
}
