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
"""Causes a high-availability Cloud SQL instance to failover to its replica."""

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Failover(base.Command):
  """Causes a high-availability Cloud SQL instance to failover."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    parser.add_argument(
        'instance',
        completion_resource='sql.instances',
        help='Cloud SQL instance ID.')
    parser.add_argument(
        '--async',
        action='store_true',
        help='Do not wait for the operation to complete.')

  def Run(self, args):
    """Calls the failover api method.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the failover
      operation if the failover was successful.
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

    instance = sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=instance_ref.project,
            instance=instance_ref.instance))

    request = sql_messages.SqlInstancesFailoverRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        instancesFailoverRequest=sql_messages.InstancesFailoverRequest(
            failoverContext=sql_messages.FailoverContext(
                kind='sql#failoverContext',
                settingsVersion=instance.settings.settingsVersion)))
    result_operation = sql_client.instances.Failover(request)

    operation_ref = resources.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project,
        instance=instance_ref.instance,)

    if args.async:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              instance=operation_ref.instance,
              operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Failing over Cloud SQL instance')

    return None
