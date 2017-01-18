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

"""deployments delete command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import dm_base
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

# Number of seconds (approximately) to wait for each delete operation to
# complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


class Delete(base.DeleteCommand):
  """Delete a deployment.

  This command deletes a deployment and deletes all associated resources.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a deployment, run:

            $ {command} my-deployment

          To issue a delete command without waiting for the operation to complete, run:

            $ {command} my-deployment --async

          To delete several deployments, run:

            $ {command} my-deployment-one my-deployment-two my-deployment-three

          To disable the confirmation prompt on delete, run:

            $ {command} my-deployment -q
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('deployment_name', nargs='+', help='Deployment name.')
    flags.AddDeletePolicyFlag(
        parser, dm_base.GetMessages().DeploymentmanagerDeploymentsDeleteRequest)
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    """Run 'deployments delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns boolean indicating whether insert operation succeeded.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    prompt_message = ('The following deployments will be deleted:\n- '
                      + '\n- '.join(args.deployment_name))
    if not args.quiet:
      if not console_io.PromptContinue(message=prompt_message, default=False):
        raise exceptions.OperationError('Deletion aborted by user.')

    operations = []
    for deployment_name in args.deployment_name:
      try:
        operation = dm_base.GetClient().deployments.Delete(
            dm_base.GetMessages().DeploymentmanagerDeploymentsDeleteRequest(
                project=dm_base.GetProject(),
                deployment=deployment_name,
                deletePolicy=(dm_base.GetMessages()
                              .DeploymentmanagerDeploymentsDeleteRequest
                              .DeletePolicyValueValuesEnum(args.delete_policy)),
            )
        )
      except apitools_exceptions.HttpError as error:
        raise api_exceptions.HttpException(error, dm_v2_util.HTTP_ERROR_FORMAT)
      if args.async:
        operations.append(operation)
      else:
        op_name = operation.name
        try:
          dm_v2_util.WaitForOperation(dm_base.GetClient(),
                                      dm_base.GetMessages(),
                                      op_name,
                                      dm_base.GetProject(),
                                      'delete',
                                      OPERATION_TIMEOUT)
          log.status.Print('Delete operation ' + op_name
                           + ' completed successfully.')
        except exceptions.OperationError as e:
          log.error(u'Delete operation {0} failed.\n{1}'.format(op_name, e))
        except apitools_exceptions.HttpError as error:
          raise api_exceptions.HttpException(error,
                                             dm_v2_util.HTTP_ERROR_FORMAT)
        try:
          completed_operation = dm_base.GetClient().operations.Get(
              dm_base.GetMessages().DeploymentmanagerOperationsGetRequest(
                  project=dm_base.GetProject(),
                  operation=op_name,
              )
          )
        except apitools_exceptions.HttpError as error:
          raise api_exceptions.HttpException(error,
                                             dm_v2_util.HTTP_ERROR_FORMAT)
        operations.append(completed_operation)

    return operations
