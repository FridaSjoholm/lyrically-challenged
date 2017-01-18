# Copyright 2015 Google Inc. All Rights Reserved.
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

"""'functions delete' command."""

from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.functions import operations
from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Deletes a given function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name', help='The name of the function to delete.',
        type=util.ValidateFunctionNameOrRaise)

  @util.CatchHTTPErrorRaiseHTTPException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None

    Raises:
      FunctionsError: If the user doesn't confirm on prompt.
    """
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    project = properties.VALUES.core.project.Get(required=True)
    name = 'projects/{0}/locations/{1}/functions/{2}'.format(
        project, args.region, args.name)

    prompt_message = 'Resource [{0}] will be deleted.'.format(name)
    if not console_io.PromptContinue(message=prompt_message):
      raise exceptions.FunctionsError('Deletion aborted by user.')
    # TODO(user): Use resources.py here after b/21908671 is fixed.
    op = client.projects_locations_functions.Delete(
        messages.CloudfunctionsProjectsLocationsFunctionsDeleteRequest(
            name=name))
    operations.Wait(op, messages, client)
    log.DeletedResource(name)
