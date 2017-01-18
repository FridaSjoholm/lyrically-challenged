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

"""deployments list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import dm_base


class List(base.ListCommand):
  """List deployments in a project.

  Prints a table with summary information on all deployments in the project.
  """

  detailed_help = {
      'EXAMPLES': """\
          To print out a list of deployments with some summary information about each, run:

            $ {command}

          To print only the name of each deployment, run:

            $ {command} --simple-list
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
    dm_v2_util.SIMPLE_LIST_FLAG.AddToParser(parser)

  def Collection(self):
    return 'deploymentmanager.deployments'

  def Run(self, args):
    """Run 'deployments list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of deployments for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    request = dm_base.GetMessages().DeploymentmanagerDeploymentsListRequest(
        project=dm_base.GetProject(),
    )
    return dm_v2_util.YieldWithHttpExceptions(list_pager.YieldFromList(
        dm_base.GetClient().deployments, request, field='deployments',
        limit=args.limit, batch_size=args.page_size))
