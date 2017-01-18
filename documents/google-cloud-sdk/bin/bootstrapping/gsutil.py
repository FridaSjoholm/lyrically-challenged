#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#

"""A convenience wrapper for starting gsutil."""

import os
import sys


import bootstrapping
from googlecloudsdk.core import config
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce as c_gce


def main():
  """Launches gsutil."""

  project, account = bootstrapping.GetActiveProjectAndAccount()
  pass_credentials = properties.VALUES.core.pass_credentials_to_gsutil.GetBool()

  if pass_credentials and account not in c_gce.Metadata().Accounts():
    gsutil_path = config.Paths().LegacyCredentialsGSUtilPath(account)

    boto_config = os.environ.get('BOTO_CONFIG', '')
    boto_path = os.environ.get('BOTO_PATH', '')

    # We construct a BOTO_PATH that tacks the refresh token config
    # on the end.
    if boto_config:
      boto_path = os.pathsep.join([boto_config, gsutil_path])
    elif boto_path:
      boto_path = os.pathsep.join([boto_path, gsutil_path])
    else:
      path_parts = ['/etc/boto.cfg',
                    os.path.expanduser(os.path.join('~', '.boto')),
                    gsutil_path]
      boto_path = os.pathsep.join(path_parts)

      if 'BOTO_CONFIG' in os.environ:
        del os.environ['BOTO_CONFIG']
      os.environ['BOTO_PATH'] = boto_path

  # Tell gsutil whether gcloud analytics collection is enabled.
  os.environ['GA_CID'] = metrics.GetCIDIfMetricsEnabled()

  args = []

  if project:
    args.extend(['-o', 'GSUtil:default_project_id=%s' % project])
  if pass_credentials and account in c_gce.Metadata().Accounts():
    # Tell gsutil to look for GCE service accounts.
    args.extend(['-o', 'GoogleCompute:service_account=default'])

  bootstrapping.ExecutePythonTool(
      'platform/gsutil', 'gsutil', *args)


if __name__ == '__main__':
  bootstrapping.CommandStart('gsutil', component_id='gsutil')

  blacklist = {
      'update': 'To update, run: gcloud components update',
  }

  bootstrapping.CheckForBlacklistedCommand(sys.argv, blacklist, warn=True,
                                           die=True)
  # Don't call bootstrapping.PreRunChecks because anonymous access is
  # supported for some endpoints. gsutil will output the appropriate
  # error message upon receiving an authentication error.
  bootstrapping.CheckUpdates('gsutil')
  main()
