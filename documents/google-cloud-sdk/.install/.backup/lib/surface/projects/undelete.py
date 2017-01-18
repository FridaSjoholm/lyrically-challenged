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

"""Command to undelete a project."""

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import log


class Undelete(base.CreateCommand):
  """Undelete a project.

  Undeletes the project with the given project ID.

  This command can fail for the following reasons:
  * There is no project with the given ID.
  * The active account does not have Owner or Editor permissions for the
    given project.

  ## EXAMPLES

  The following command undeletes the project with the ID `example-foo-bar-1`:

    $ {command} example-foo-bar-1
  """

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        help='ID for the project you want to undelete.')

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Undelete(project_ref)
    log.RestoredResource(project_ref, kind='project')
    return result
