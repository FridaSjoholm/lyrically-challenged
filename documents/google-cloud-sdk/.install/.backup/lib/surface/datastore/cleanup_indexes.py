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

"""The gcloud datstore cleanup-indexes command."""

from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class CleanupIndexes(base.Command):

  detailed_help = {
      'brief': 'Remove unused datastore indexes based on your local index '
               'configuration.',
      'DESCRIPTION': """
This command removes unused datastore indexes based on your local index
configuration. Any indexes that exist that are not in the index file will be
removed.
      """,
      'EXAMPLES': """\
          To remove unused indexes based on your local configuration, run:

            $ {command} ~/myapp/index.yaml
          """,
  }

  @staticmethod
  def Args(parser):
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    parser.add_argument('index_file',
                        help='The path to your index.yaml file.')

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    app_config = yaml_parsing.AppConfigSet([args.index_file])

    if yaml_parsing.ConfigYamlInfo.INDEX not in app_config.Configs():
      raise exceptions.InvalidArgumentException(
          'index_file', 'You must provide the path to a valid index.yaml file.')

    info = app_config.Configs()[yaml_parsing.ConfigYamlInfo.INDEX]
    output_helpers.DisplayProposedConfigDeployments(project, [info])
    console_io.PromptContinue(default=True, throw_if_unattended=False,
                              cancel_on_no=True)

    client = appengine_client.AppengineClient()
    client.CleanupIndexes(info.parsed)
