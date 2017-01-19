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
"""Deletes a Cloud SQL instance."""

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import remote_completion
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Deletes a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'instance',
        completion_resource='sql.instances',
        help='Cloud SQL instance ID.')

  def Run(self, args):
    """Deletes a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the delete was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']
    operation_ref = None

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    if not console_io.PromptContinue(
        'All of the instance data will be lost when the instance is deleted.'):
      return None
    try:
      result = sql_client.instances.Delete(
          sql_messages.SqlInstancesDeleteRequest(
              instance=instance_ref.instance,
              project=instance_ref.project))

      operation_ref = resources.Create(
          'sql.operations',
          operation=result.operation,
          project=instance_ref.project,
          instance=instance_ref.instance,
      )

      log.DeletedResource(instance_ref)
      cache = remote_completion.RemoteCompletion()
      cache.DeleteFromCache(instance_ref.SelfLink())

    except exceptions.HttpError:
      log.debug('operation : %s', str(operation_ref))
      raise


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(base.Command):
  """Deletes a Cloud SQL instance."""

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

  def Run(self, args):
    """Deletes a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the delete was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']
    operation_ref = None

    validate.ValidateInstanceName(args.instance)
    instance_ref = resources.Parse(args.instance, collection='sql.instances')

    if not console_io.PromptContinue(
        'All of the instance data will be lost when the instance is deleted.'):
      return None
    try:
      result = sql_client.instances.Delete(
          sql_messages.SqlInstancesDeleteRequest(
              instance=instance_ref.instance,
              project=instance_ref.project))

      operation_ref = resources.Create(
          'sql.operations',
          operation=result.name,
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
          sql_client, operation_ref, 'Deleting Cloud SQL instance')

      log.DeletedResource(instance_ref)
      cache = remote_completion.RemoteCompletion()
      cache.DeleteFromCache(instance_ref.SelfLink())

    except exceptions.HttpError:
      log.debug('operation : %s', str(operation_ref))
      raise
