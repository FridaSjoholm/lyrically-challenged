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

"""Creates a new Cloud SQL instance."""
import argparse

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.sql import instances
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import remote_completion
from googlecloudsdk.core.console import console_io


class _BaseCreate(object):
  """Create command base class for all release tracks."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--activation-policy',
        required=False,
        choices=['ALWAYS', 'NEVER', 'ON_DEMAND'],
        default=None,
        help='The activation policy for this instance. This specifies when the '
        'instance should be activated and is applicable only when the '
        'instance state is RUNNABLE.')
    parser.add_argument(
        '--assign-ip',
        required=False,
        action='store_true',
        default=None,  # Tri-valued: None => don't change the setting.
        help='Specified if the instance must be assigned an IP address.')
    parser.add_argument(
        '--authorized-gae-apps',
        type=arg_parsers.ArgList(min_length=1),
        metavar='APP',
        required=False,
        default=[],
        help='List of App Engine app IDs that can access this instance.')
    parser.add_argument(
        '--authorized-networks',
        type=arg_parsers.ArgList(min_length=1),
        metavar='NETWORK',
        required=False,
        default=[],
        help='The list of external networks that are allowed to connect to the'
        ' instance. Specified in CIDR notation, also known as \'slash\' '
        'notation (e.g. 192.168.100.0/24).')
    parser.add_argument(
        '--backup-start-time',
        required=False,
        help='The start time of daily backups, specified in the 24 hour format '
        '- HH:MM, in the UTC timezone.')
    parser.add_argument(
        '--backup',
        required=False,
        action='store_true',
        default=True,
        help='Enables daily backup.')
    parser.add_argument(
        '--database-version',
        required=False,
        default='MYSQL_5_6',
        help='The database engine type and version. Can be MYSQL_5_5, '
        'MYSQL_5_6, or MYSQL_5_7.')
    parser.add_argument(
        '--enable-bin-log',
        required=False,
        action='store_true',
        default=None,  # Tri-valued: None => don't change the setting.
        help='Specified if binary log should be enabled. If backup '
        'configuration is disabled, binary log must be disabled as well.')
    parser.add_argument(
        '--follow-gae-app',
        required=False,
        help='The App Engine app this instance should follow. It must be in '
        'the same region as the instance.')
    parser.add_argument(
        '--gce-zone',
        required=False,
        help='The preferred Compute Engine zone (e.g. us-central1-a, '
        'us-central1-b, etc.).')
    parser.add_argument(
        'instance',
        help='Cloud SQL instance ID.')
    parser.add_argument(
        '--master-instance-name',
        required=False,
        help='Name of the instance which will act as master in the replication '
        'setup. The newly created instance will be a read replica of the '
        'specified master instance.')
    parser.add_argument(
        '--on-premises-host-port',
        required=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--pricing-plan',
        '-p',
        required=False,
        choices=['PER_USE', 'PACKAGE'],
        default='PER_USE',
        help='The pricing plan for this instance.')
    # TODO(b/31989340): add remote completion
    parser.add_argument(
        '--region',
        required=False,
        default='us-central',
        help='The regional location '
        '(e.g. asia-east1, us-east1). See the full list of regions at '
        'https://cloud.google.com/sql/docs/instance-locations.')
    parser.add_argument(
        '--replication',
        required=False,
        choices=['SYNCHRONOUS', 'ASYNCHRONOUS'],
        default=None,
        help='The type of replication this instance uses.')
    parser.add_argument(
        '--require-ssl',
        required=False,
        action='store_true',
        default=None,  # Tri-valued: None => don't change the setting.
        help='Specified if users connecting over IP must use SSL.')
    parser.add_argument(
        '--tier',
        '-t',
        required=False,
        default='D1',
        help='The tier of service for this instance, for example D0, D1.')
    parser.add_argument(
        '--database-flags',
        type=arg_parsers.ArgDict(min_length=1),
        metavar='FLAG=VALUE',
        required=False,
        help='A comma-separated list of database flags to set on the instance. '
        'Use an equals sign to separate flag name and value. Flags without '
        'values, like skip_grant_tables, can be written out without a value '
        'after, e.g., `skip_grant_tables=`. Use on/off for '
        'booleans. View the Instance Resource API for allowed flags. '
        '(e.g., `--database-flags max_allowed_packet=55555,skip_grant_tables=,'
        'log_output=1`)')

  def Format(self, args):
    return self.ListFormat(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(_BaseCreate, base.Command):
  """Creates a new Cloud SQL instance."""

  def Collection(self):
    return 'sql.instances'

  def Run(self, args):
    """Creates a new Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
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
    instance_resource = instances.InstancesV1Beta3.ConstructInstanceFromArgs(
        sql_messages, args, instance_ref=instance_ref)

    if args.pricing_plan == 'PACKAGE':
      if not console_io.PromptContinue(
          'Charges will begin accruing immediately. Really create Cloud '
          'SQL instance?'):
        raise exceptions.ToolException('canceled by the user.')

    operation_ref = None
    try:
      result = sql_client.instances.Insert(instance_resource)

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
          sql_client, operation_ref, 'Creating Cloud SQL instance')

      log.CreatedResource(instance_ref)

      new_resource = sql_client.instances.Get(
          sql_messages.SqlInstancesGetRequest(
              project=instance_ref.project,
              instance=instance_ref.instance))
      cache = remote_completion.RemoteCompletion()
      cache.AddToCache(instance_ref.SelfLink())
      return new_resource
    except apitools_exceptions.HttpError:
      log.debug('operation : %s', str(operation_ref))
      raise


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(_BaseCreate, base.Command):
  """Creates a new Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    _BaseCreate.Args(parser)
    parser.add_argument(
        '--storage-type',
        required=False,
        choices=['SSD', 'HDD'],
        default=None,
        help='The storage type for the instance.')
    parser.add_argument(
        '--failover-replica-name',
        required=False,
        help='Also create a failover replica with the specified name.')
    base.Argument(
        '--storage-auto-increase',
        action='store_true',
        default=None,
        help='Adds storage capacity whenever space is low. Up to 25 GB per '
        'increase. All increases are permanent.',
        detailed_help='Storage size can be increased, but it cannot be '
        'decreased; storage increases are permanent for the life of the '
        'instance. With this setting enabled, a spike in storage requirements '
        'can result in permanently increased storage costs for your instance. '
        'However, if an instance runs out of available space, it can result in '
        'the instance going offline, dropping existing connections.'
    ).AddToParser(parser)
    parser.add_argument(
        '--replica-type',
        choices=['READ', 'FAILOVER'],
        help='The type of replica to create.')
    parser.add_argument(
        '--storage-size',
        type=arg_parsers.BinarySize(lower_bound='10GB', upper_bound='10230GB',
                                    suggested_binary_size_scales=['GB']),
        help='Amount of storage allocated to the instance. Must be an integer '
             'number of GB between 10GB and 10230GB inclusive.')
    parser.add_argument(
        '--maintenance-release-channel',
        choices={'production': 'Production updates are stable and recommended '
                               'for applications in production.',
                 'preview': 'Preview updates release prior to production '
                            'updates. You may wish to use the preview channel '
                            'for dev/test applications so that you can preview '
                            'their compatibility with your application prior '
                            'to the production release.'},
        type=str.lower,
        help="Which channel's updates to apply during the maintenance window.")
    parser.add_argument(
        '--maintenance-window-day',
        choices=arg_parsers.DayOfWeek.DAYS,
        type=arg_parsers.DayOfWeek.Parse,
        help='Day of week for maintenance window, in UTC time zone.')
    parser.add_argument(
        '--maintenance-window-hour',
        type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=23),
        help='Hour of day for maintenance window, in UTC time zone.')

  def Collection(self):
    return 'sql.instances.v1beta4'

  def Run(self, args):
    """Creates a new Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
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
    instance_resource = instances.InstancesV1Beta4.ConstructInstanceFromArgs(
        sql_messages, args, instance_ref=instance_ref)

    if args.pricing_plan == 'PACKAGE':
      if not console_io.PromptContinue(
          'Charges will begin accruing immediately. Really create Cloud '
          'SQL instance?'):
        raise exceptions.ToolException('canceled by the user.')

    operation_ref = None
    try:
      result_operation = sql_client.instances.Insert(instance_resource)

      operation_ref = resources.Create(
          'sql.operations',
          operation=result_operation.name,
          project=instance_ref.project)

      if args.async:
        return sql_client.operations.Get(
            sql_messages.SqlOperationsGetRequest(
                project=operation_ref.project,
                operation=operation_ref.operation))

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref, 'Creating Cloud SQL instance')

      log.CreatedResource(instance_ref)

      new_resource = sql_client.instances.Get(
          sql_messages.SqlInstancesGetRequest(
              project=instance_ref.project,
              instance=instance_ref.instance))
      cache = remote_completion.RemoteCompletion()
      cache.AddToCache(instance_ref.SelfLink())
      return new_resource
    except apitools_exceptions.HttpError:
      log.debug('operation : %s', str(operation_ref))
      raise
