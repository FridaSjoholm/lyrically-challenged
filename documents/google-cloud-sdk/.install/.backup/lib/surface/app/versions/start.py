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

"""The Start command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_printer


class VersionsStartError(exceptions.Error):
  """Errors occurring when starting versions."""
  pass


class Start(base.Command):
  """Start serving specified versions.

  This command starts serving the specified versions. It may only be used if the
  scaling module for your service has been set to manual.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To start a specific version across all services, run:

            $ {command} v1

          To start multiple named versions across all services, run:

            $ {command} v1 v2

          To start a single version on a single service, run:

            $ {command} --service servicename v1

          To start multiple versions in a single service, run:

            $ {command} --service servicename v1 v2
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('versions', nargs='+', help=(
        'The versions to start. (optionally filtered by the --service flag).'))
    parser.add_argument('--service', '-s',
                        help=('If specified, only start versions from the '
                              'given service.'))

  def Run(self, args):
    # TODO(user): This fails with "module/version does not exist" even
    # when it exists if the scaling mode is set to auto.  It would be good
    # to improve that error message.
    api_client = appengine_api_client.GetApiClient()
    services = api_client.ListServices()
    versions = version_util.GetMatchingVersions(
        api_client.ListVersions(services),
        args.versions, args.service)

    if not versions:
      log.warn('No matching versions found.')
      return

    fmt = 'list[title="Starting the following versions:"]'
    resource_printer.Print(versions, fmt, out=log.status)
    console_io.PromptContinue(cancel_on_no=True)

    errors = {}
    # Sort versions to make behavior deterministic enough for unit testing.
    for version in sorted(versions):
      try:
        with progress_tracker.ProgressTracker('Starting [{0}]'.format(version)):
          api_client.StartVersion(version.service, version.id)
      except (calliope_exceptions.HttpException,
              operations_util.OperationError,
              operations_util.OperationTimeoutError) as err:
        errors[version] = str(err)
    if errors:
      printable_errors = {}
      for version, error_msg in errors.items():
        short_name = '[{0}/{1}]'.format(version.service, version.id)
        printable_errors[short_name] = '{0}: {1}'.format(short_name, error_msg)
      raise VersionsStartError(
          'Issues starting version(s): {0}\n\n'.format(
              ', '.join(printable_errors.keys())) +
          '\n\n'.join(printable_errors.values()))
