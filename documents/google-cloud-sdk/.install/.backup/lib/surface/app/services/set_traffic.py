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
"""`gcloud app services set-traffic` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer


class TrafficSplitError(exceptions.Error):
  """Errors occurring when setting traffic splits."""
  pass


class SetTraffic(base.Command):
  """Set traffic splitting settings.

  This command sets the traffic split of versions across a service or a project.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To send all traffic to 'v2' of service 's1', run:

            $ {command} s1 --splits v2=1

          To split traffic evenly between 'v1' and 'v2' of service 's1', run:

            $ {command} s1 --splits v2=.5,v1=.5

          To split traffic across all services:

            $ {command} --splits v2=.5,v1=.5
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('services', nargs='*', help=(
        'The services to modify.'))
    splits = parser.add_argument(
        '--splits',
        required=True,
        type=arg_parsers.ArgDict(min_length=1),
        help='List of key value pairs containing versions '
             'and their proportional traffic split.')
    splits.detailed_help = (
        'Key-value pairs describing what proportion of traffic should go to '
        'each version. The split values are added together and used as '
        'weights. The exact values do not matter, only their relation to each '
        'other. For example, v1=2,v2=2 is equivalent to v1=.5,v2=.5')
    parser.add_argument(
        '--split-by',
        choices=['cookie', 'ip'],
        default='ip',
        help='Whether to split traffic based on cookies or IP addresses.')
    migrate = parser.add_argument(
        '--migrate',
        action='store_true',
        default=False,
        help='Whether to use traffic migration during the operation.')
    migrate.detailed_help = (
        'The migrate flag determines whether or not to use traffic migration '
        'during the operation. Traffic migration will attempt to automatically '
        'migrate traffic from the previous version to the new version, giving '
        'the autoscaler time to respond. See the documentation here: '
        '[](https://cloud.google.com/appengine/docs/python/console/'
        'trafficmigration) for more information.'
    )

  def Run(self, args):
    if args.migrate and len(args.splits) > 1:
      raise TrafficSplitError('The migrate flag can only be used with splits '
                              'to a single version.')

    api_client = appengine_api_client.GetApiClient()

    all_services = api_client.ListServices()
    services = service_util.GetMatchingServices(all_services, args.services)

    allocations = service_util.ParseTrafficAllocations(
        args.splits, args.split_by)

    display_allocations = []
    for service in services:
      for version, split in allocations.iteritems():
        display_allocations.append('{0}/{1}/{2}: {3}'.format(
            api_client.project,
            service.id,
            version,
            split))

    fmt = 'list[title="Setting the following traffic allocations:"]'
    resource_printer.Print(display_allocations, fmt, out=log.status)
    log.status.Print('Any other versions on the specified services will '
                     'receive zero traffic.')
    console_io.PromptContinue(cancel_on_no=True)

    errors = {}
    for service in services:
      try:
        api_client.SetTrafficSplit(
            service.id, allocations, args.split_by.upper(), args.migrate)
      except (calliope_exceptions.HttpException,
              operations_util.OperationError,
              operations_util.OperationTimeoutError) as err:
        errors[service.id] = str(err)
    if errors:
      printable_errors = {}
      for service, error_msg in errors.items():
        printable_errors[service] = error_msg
      raise TrafficSplitError(
          'Issue setting traffic on service(s): {0}\n\n'.format(
              ', '.join(printable_errors.keys())) +
          '\n\n'.join(printable_errors.values()))
