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
"""`gcloud app versions list` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class ServiceNotFoundError(exceptions.Error):
  pass


class List(base.ListCommand):
  """List your existing versions.

  This command lists all the versions of all services that are currently
  deployed to the App Engine server.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all services and versions, run:

            $ {command}

          To list all versions for a specific service, run:

            $ {command} --service service1

          To list only versions that are receiving traffic, run:

            $ {command} --hide-no-traffic
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--service', '-s',
                        help='Only show versions from this service.')
    parser.add_argument('--hide-no-traffic', action='store_true',
                        help='Only show versions that are receiving traffic.')

  def Collection(self):
    return 'appengine.versions'

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    services = api_client.ListServices()
    service_ids = [s.id for s in services]
    log.debug('All services: {0}'.format(service_ids))

    if args.service and args.service not in service_ids:
      raise ServiceNotFoundError(
          'Service [{0}] not found.'.format(args.service))

    # Filter the services list to make fewer ListVersions calls.
    if args.service:
      services = [s for s in services if s.id == args.service]

    versions = api_client.ListVersions(services)
    # Filter for service.
    if args.service:
      versions = [v for v in versions if v.service == args.service]

    # Filter for traffic.
    if args.hide_no_traffic:
      versions = [v for v in versions if v.traffic_split]
    return sorted(versions)
