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

"""The command to list installed/available gcloud components."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer_base


class List(base.ListCommand):
  """List the status of all Cloud SDK components.

  List all components in the Cloud SDK and provide information such as whether
  the component is installed on the local workstation, whether a newer version
  is available, the size of the component, and the ID used to refer to the
  component in commands.
  """
  detailed_help = {
      'DESCRIPTION': """\
          This command lists all the available components in the Cloud SDK. For
          each component, the command lists the following information:

          * Status on your local workstation: not installed, installed (and
            up to date), and update available (installed, but not up to date)
          * Name of the component (a description)
          * ID of the component (used to refer to the component in other
            [{parent_command}] commands)
          * Size of the component

          In addition, if the `--show-versions` flag is specified, the command
          lists the currently installed version (if any) and the latest
          available version of each individual component.
      """,
      'EXAMPLES': """\
            $ {command}

            $ {command} --show-versions
      """,
  }

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--show-versions', required=False, action='store_true',
        help='Show installed and available versions of all components.')

  def Format(self, args):
    attributes = [
        'box',
        'title="Components"'
        ]
    columns = [
        'state.name:label=Status',
        'name:label=Name',
        ]
    if args.show_versions:
      columns.extend([
          'current_version_string:label=Installed:align=right',
          'latest_version_string:label=Latest:align=right',
          ])
    columns.extend([
        'id:label=ID',
        'size.size(zero="",min=1048576):label=Size:align=right',
        ])
    return 'table[{attributes}]({columns})'.format(
        attributes=','.join(attributes), columns=','.join(columns))

  def Run(self, args):
    """Runs the list command."""
    update_manager = util.GetUpdateManager(args)
    result = update_manager.List()
    (to_print, self._current_version, self._latest_version) = result
    if not to_print:
      raise StopIteration

    for c in to_print:
      yield c
    yield resource_printer_base.FinishMarker()

  def Epilog(self, resources_were_displayed):
    if not resources_were_displayed:
      log.status.write('\nNo updates.')
    log.status.write("""\
To install or remove components at your current SDK version [{current}], run:
  $ gcloud components install COMPONENT_ID
  $ gcloud components remove COMPONENT_ID

To update your SDK installation to the latest version [{latest}], run:
  $ gcloud components update

""".format(current=self._current_version, latest=self._latest_version))
