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
"""gcloud dns record-sets import command."""

import os
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dns import import_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.UnicodeIsSupported
class Import(base.Command):
  """Import record-sets into your managed-zone.

  This command imports record-sets contained within the specified record-sets
  file into your managed-zone. Note that NS records for the origin of the zone,
  and the SOA NS field, are not imported since name-servers are managed by
  Cloud DNS. By default, record-sets cannot be imported if there are any
  conflicts. A conflict exists if an existing record-set has the same name and
  type as a record-set that is being imported. In contrast, if the
  --delete-all-existing flag is used, the imported record-sets will replace all
  the records-sets currently in the managed-zone.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To import record-sets from a yaml record-sets file, run:

            $ {command} YAML_RECORDS_FILE -z MANAGED_ZONE

          To import record-sets from a zone file, run:

            $ {command} ZONE_FILE --zone-file-format -z MANAGED_ZONE

          To replace all the record-sets in your zone with records from a yaml
          file, run:

            $ {command} YAML_RECORDS_FILE --delete-all-existing -z MANAGED_ZONE
          """,
  }

  @staticmethod
  def Args(parser):
    util.ZONE_FLAG.AddToParser(parser)
    parser.add_argument('records_file',
                        help='File from which record-sets should be imported.')
    parser.add_argument(
        '--zone-file-format',
        required=False,
        action='store_true',
        help='Indicates that the records-file is in the zone file format.')
    parser.add_argument(
        '--delete-all-existing',
        required=False,
        action='store_true',
        help='Indicates that all existing record-sets should be deleted before'
        ' importing the record-sets in the records-file.')
    parser.add_argument(
        '--replace-origin-ns',
        required=False,
        action='store_true',
        help='Indicates that NS records for the origin of a zone should be'
        ' imported if defined')

  def Collection(self):
    return 'dns.changes'

  def Format(self, args):
    return self.ListFormat(args)

  def Run(self, args):
    if not os.path.exists(args.records_file):
      raise exceptions.ToolException(
          'no such file [{0}]'.format(args.records_file))
    if os.path.isdir(args.records_file):
      raise exceptions.ToolException(
          '[{0}] is a directory'.format(args.records_file))

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

    # Get the current record-sets.
    current = {}
    for record in list_pager.YieldFromList(
        dns.resourceRecordSets,
        messages.DnsResourceRecordSetsListRequest(project=project_id,
                                                  managedZone=zone_ref.Name()),
        field='rrsets'):
      current[(record.name, record.type)] = record

    # Get the imported record-sets.
    try:
      with open(args.records_file) as import_file:
        if args.zone_file_format:
          imported = import_util.RecordSetsFromZoneFile(import_file,
                                                        zone.dnsName)
        else:
          imported = import_util.RecordSetsFromYamlFile(import_file)
    except Exception as exp:
      msg = (u'unable to read record-sets from specified records-file [{0}] '
             u'because [{1}]')
      msg = msg.format(args.records_file, exp.message)
      raise exceptions.ToolException(msg)

    # Get the change resulting from the imported record-sets.
    change = import_util.ComputeChange(current, imported,
                                       args.delete_all_existing,
                                       zone.dnsName, args.replace_origin_ns)
    if not change:
      msg = u'Nothing to do, all the records in [{0}] already exist.'.format(
          args.records_file)
      log.status.Print(msg)
      return None

    # Send the change to the service.
    result = dns.changes.Create(
        messages.DnsChangesCreateRequest(change=change,
                                         managedZone=zone.name,
                                         project=project_id))
    change_ref = resources.Create(collection='dns.changes',
                                  project=project_id,
                                  managedZone=zone.name,
                                  changeId=result.id)
    msg = u'Imported record-sets from [{0}] into managed-zone [{1}].'.format(
        args.records_file, zone_ref.Name())
    log.status.Print(msg)
    log.CreatedResource(change_ref)
    return result
