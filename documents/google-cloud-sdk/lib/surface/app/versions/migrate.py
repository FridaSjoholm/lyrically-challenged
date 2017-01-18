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

"""The Migrate command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class VersionsMigrateError(exceptions.Error):
  """Errors when migrating versions."""


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Migrate(base.Command):
  """Migrate traffic from one version to another for a set of services."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          This only works for automatically scaled Standard versions.
          To migrate from one version to another for all services where there
          is a version v2 and shut down the previous version, run:

            $ {command} v2

          To migrate from one version to another for a specific service, run:

            $ {command} v2 --service="s1"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('version', help='The version to migrate to.')
    parser.add_argument('--service', '-s',
                        help='If specified, only migrate versions from the '
                             'given service.')

  def Run(self, args):
    client = appengine_api_client.GetApiClient()
    if args.service:
      service = client.GetServiceResource(args.service)
      traffic_split = {}
      if service.split:
        for split in service.split.allocations.additionalProperties:
          traffic_split[split.key] = split.value
      services = [service_util.Service(client.project, service.id,
                                       traffic_split)]
    else:
      services = client.ListServices()
    all_versions = client.ListVersions(services)
    if args.version not in {v.id for v in all_versions}:
      if args.service:
        raise VersionsMigrateError('Version [{0}/{1}] does not exist.'.format(
            args.service, args.version))
      else:
        raise VersionsMigrateError('Version [{0}] does not exist.'.format(
            args.version))
    service_names = {v.service for v in all_versions if v.id == args.version}

    def WillBeMigrated(v):
      return (v.service in service_names and v.traffic_split and
              v.traffic_split > 0 and v.id != args.version)

    # All versions that will stop receiving traffic.
    versions_to_migrate = filter(WillBeMigrated, all_versions)

    for version in versions_to_migrate:
      short_name = '{0}/{1}'.format(version.service, version.id)
      promoted_name = '{0}/{1}'.format(version.service, args.version)
      log.status.Print('Migrating all traffic from version '
                       '[{0}] to [{1}]'.format(
                           short_name, promoted_name))

    console_io.PromptContinue(cancel_on_no=True)

    errors = {}
    for service in sorted(set([v.service for v in versions_to_migrate])):
      allocations = {args.version: 1.0}
      try:
        client.SetTrafficSplit(service, allocations,
                               shard_by='ip', migrate=True)
      except (api_exceptions.HttpException,
              operations_util.OperationError,
              operations_util.OperationTimeoutError, util.RPCError) as e:
        errors[service] = str(e)

    if errors:
      error_string = ('Issues migrating all traffic of '
                      'service(s): [{0}]\n\n{1}'.format(
                          ', '.join(errors.keys()),
                          '\n\n'.join(errors.values())))
      raise VersionsMigrateError(error_string)
