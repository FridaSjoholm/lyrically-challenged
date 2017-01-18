#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#

"""A convenience wrapper for starting bq."""

import os
import sys

import bootstrapping

from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import gce


def main():
  """Launches bq."""

  project, account = bootstrapping.GetActiveProjectAndAccount()
  adc_path = config.Paths().LegacyCredentialsAdcPath(account)
  single_store_path = config.Paths().LegacyCredentialsSingleStorePath(account)

  gce_metadata = gce.Metadata()
  if gce_metadata and account in gce_metadata.Accounts():
    args = ['--use_gce_service_account']
  elif os.path.isfile(adc_path):
    args = ['--application_default_credential_file', adc_path,
            '--credential_file', single_store_path]
  else:
    p12_key_path = config.Paths().LegacyCredentialsP12KeyPath(account)
    if os.path.isfile(p12_key_path):
      args = ['--service_account', account,
              '--service_account_credential_file', single_store_path,
              '--service_account_private_key_file', p12_key_path]
    else:
      args = []  # Don't have any credentials we can pass.

  if project:
    args += ['--project', project]

  bootstrapping.ExecutePythonTool(
      'platform/bq', 'bq.py', *args)


if __name__ == '__main__':
  bootstrapping.CommandStart('bq', component_id='bq')
  blacklist = {
      'init': 'To authenticate, run gcloud auth.',
  }
  bootstrapping.CheckForBlacklistedCommand(sys.argv, blacklist,
                                           warn=True, die=True)
  bootstrapping.CheckCredOrExit(can_be_gce=True)
  bootstrapping.CheckUpdates('bq')
  main()
