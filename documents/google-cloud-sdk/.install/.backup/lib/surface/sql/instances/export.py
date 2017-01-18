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

"""Exports data from a Cloud SQL instance.

Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as
a MySQL dump file.
"""

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class _BaseExport(object):
  """Exports data from a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'instance',
        completion_resource='sql.instances',
        help='Cloud SQL instance ID.')
    parser.add_argument(
        'uri',
        help='The path to the file in Google Cloud Storage where the export '
        'will be stored. The URI is in the form gs://bucketName/fileName. '
        'If the file already exists, the operation fails. If the filename '
        'ends with .gz, the contents are compressed.')
    parser.add_argument(
        '--database',
        '-d',
        type=arg_parsers.ArgList(min_length=1),
        metavar='DATABASE',
        required=False,
        help='Database (for example, guestbook) from which the export is made.'
        ' If unspecified, all databases are exported.')
    parser.add_argument(
        '--table',
        '-t',
        type=arg_parsers.ArgList(min_length=1),
        metavar='TABLE',
        required=False,
        help='Tables to export from the specified database. If you specify '
        'tables, specify one and only one database.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Export(_BaseExport, base.Command):
  """Exports data from a Cloud SQL instance.

  Exports data from a Cloud SQL instance to a Google Cloud Storage
  bucket as a MySQL dump file.
  """

  def Run(self, args):
    """Exports data from a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the export
      operation if the export was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    export_request = sql_messages.SqlInstancesExportRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesExportRequest=sql_messages.InstancesExportRequest(
            exportContext=sql_messages.ExportContext(
                uri=args.uri,
                database=args.database or [],
                table=args.table or [],
            ),
        ),
    )

    result = sql_client.instances.Export(export_request)

    operation_ref = resources.Create(
        'sql.operations',
        operation=result.operation,
        project=instance_ref.project,
        instance=instance_ref.instance,
    )

    if args.async:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              instance=operation_ref.instance,
              operation=operation_ref.operation))

    operations.OperationsV1Beta3.WaitForOperation(
        sql_client, operation_ref, 'Exporting Cloud SQL instance')

    log.status.write('Exported [{instance}] to [{bucket}].\n'.format(
        instance=instance_ref, bucket=args.uri))

    return None


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ExportBeta(_BaseExport, base.Command):
  """Exports data from a Cloud SQL instance.

  Exports data from a Cloud SQL instance to a Google Cloud Storage
  bucket as a MySQL dump file.
  """

  def Run(self, args):
    """Exports data from a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the export
      operation if the export was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    # TODO(user): add support for CSV exporting.
    export_request = sql_messages.SqlInstancesExportRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesExportRequest=sql_messages.InstancesExportRequest(
            exportContext=sql_messages.ExportContext(
                uri=args.uri,
                databases=args.database or [],
                fileType='SQL',
                sqlExportOptions=(
                    sql_messages.ExportContext.SqlExportOptionsValue(
                        tables=args.table or [],
                    )),
            ),
        ),
    )

    result_operation = sql_client.instances.Export(export_request)

    operation_ref = resources.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project,
        instance=instance_ref.instance,
    )

    if args.async:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              instance=operation_ref.instance,
              operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Exporting Cloud SQL instance')

    log.status.write('Exported [{instance}] to [{bucket}].\n'.format(
        instance=instance_ref, bucket=args.uri))

    return None
