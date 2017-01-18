# Copyright 2014 Google Inc. All Rights Reserved.
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
"""gcloud dns record-sets export command."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dns import export_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Export(base.Command):
  """Export your record-sets into a file.

  This command exports the record-sets contained within the specified
  managed-zone into a file.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To export record-sets into a yaml file, run:

            $ {command} YAML_RECORDS_FILE -z MANAGED_ZONE

          To import record-sets into a zone file, run:

            $ {command} ZONE_FILE --zone-file-format -z MANAGED_ZONE
          """,
  }

  @staticmethod
  def Args(parser):
    util.ZONE_FLAG.AddToParser(parser)
    parser.add_argument('records_file',
                        help='File to which record-sets should be exported.')
    parser.add_argument(
        '--zone-file-format',
        required=False,
        action='store_true',
        help='Indicates that records-file should be in the zone file format.')

  def Run(self, args):
    dns = self.context['dns_client']
    messages = self.context['dns_messages']
    resources = self.context['dns_resources']
    project_id = properties.VALUES.core.project.Get(required=True)

    # Get the managed-zone.
    zone_ref = resources.Parse(args.zone, collection='dns.managedZones')
    try:
      zone = dns.managedZones.Get(
          dns.MESSAGES_MODULE.DnsManagedZonesGetRequest(
              project=zone_ref.project,
              managedZone=zone_ref.managedZone))
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

    # Get all the record-sets.
    record_sets = []
    for record_set in list_pager.YieldFromList(
        dns.resourceRecordSets,
        messages.DnsResourceRecordSetsListRequest(project=project_id,
                                                  managedZone=zone_ref.Name()),
        field='rrsets'):
      record_sets.append(record_set)

    # Export the record-sets.
    try:
      with open(args.records_file, 'w') as export_file:
        if args.zone_file_format:
          export_util.WriteToZoneFile(export_file, record_sets, zone.dnsName)
        else:
          export_util.WriteToYamlFile(export_file, record_sets)
    except Exception as exp:
      msg = 'unable to export record-sets to file [{0}]: {1}'.format(
          args.records_file, exp)
      raise exceptions.ToolException(msg)

    log.status.Print('Exported record-sets to [{0}].'.format(args.records_file))
