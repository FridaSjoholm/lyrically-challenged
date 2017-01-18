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

"""The runtime-configs variables unset command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager.runtime_configs import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager.runtime_configs import flags
from googlecloudsdk.core import log


class Unset(base.DeleteCommand):
  """Delete variable resources.

  This command deletes the variable resource with the specified name.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To delete a variable named "my-var", run:

            $ {command} --config-name my-config my-var

          To delete a variable, but fail if it does not exist, run:

            $ {command} --config-name my-config my-var --fail-if-absent

          To recursively delete a parent variable and its children, run:

            $ {command} --config-name my-config my-parent-var --recursive
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
    flags.AddConfigFlag(parser)

    parser.add_argument(
        '--fail-if-absent',
        help='Fail if a variable with the specified name does not exist.',
        action='store_true')

    parser.add_argument(
        '--recursive',
        help='Delete a parent node and all of its children.',
        action='store_true')

    parser.add_argument('name', help='The variable name.')

  def Collection(self):
    """Returns the default collection path string.

    Returns:
      The default collection path string.
    """
    return 'runtimeconfig.variables'

  def Run(self, args):
    """Run 'runtime-configs variables set'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The new variable.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    variable_client = util.VariableClient()
    messages = util.Messages()

    var_resource = util.ParseVariableName(args.name, args)

    try:
      variable_client.Delete(
          messages.RuntimeconfigProjectsConfigsVariablesDeleteRequest(
              name=var_resource.RelativeName(),
              recursive=args.recursive,
          )
      )

      log.DeletedResource(var_resource)

    except apitools_exceptions.HttpError as error:
      # Raise this failure if the user requested it, or if the
      # error is not a 404.
      if not util.IsNotFoundError(error) or args.fail_if_absent:
        raise
