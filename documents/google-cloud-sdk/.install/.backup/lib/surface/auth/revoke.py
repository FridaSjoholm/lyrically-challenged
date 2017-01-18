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

"""Revoke credentials being used by the CloudSDK."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store


class Revoke(base.Command):
  """Revoke access credentials for an account.

  Revokes credentials for the specified user accounts or service accounts.
  When you revoke the credentials, they are removed from the local machine. If
  no account is specified, this command revokes credentials for the currently
  active account.

  You can revoke credentials when you want to disallow access by gcloud and
  other Cloud SDK tools using a specified account. You don't need to revoke
  credentials to switch between accounts.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('accounts', nargs='*',
                        help='Accounts whose credentials are to be revoked.')
    parser.add_argument('--all', action='store_true',
                        help='Revoke credentials for all accounts.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Revoke credentials and update active account."""
    accounts = args.accounts or []
    if type(accounts) is str:
      accounts = [accounts]
    available_accounts = c_store.AvailableAccounts()
    unknown_accounts = set(accounts) - set(available_accounts)
    if unknown_accounts:
      raise c_exc.UnknownArgumentException(
          'accounts', ' '.join(unknown_accounts))
    if args.all:
      accounts = available_accounts

    active_account = properties.VALUES.core.account.Get()

    if not accounts and active_account:
      accounts = [active_account]

    if not accounts:
      raise c_exc.InvalidArgumentException(
          'accounts', 'No credentials available to revoke.')

    for account in accounts:
      if active_account == account:
        properties.PersistProperty(properties.VALUES.core.account, None)
      if not c_store.Revoke(account):
        log.warn('[{}] already inactive (previously revoked?)'.format(account))
    return accounts

  def Format(self, unused_args):
    return 'list[title="Revoked credentials:"]'

  def Epilog(self, unused_results_were_displayed):
    log_out = log.out
    log.out = log.status
    self.ExecuteCommand(['auth', 'list'])
    log.out = log_out
