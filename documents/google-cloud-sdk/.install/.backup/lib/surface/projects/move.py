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
"""Command to move a project into an organization."""

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags as project_flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import flags as folder_flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Move(base.Command):
  """Move a project into an organization.

  Moves the given project into the given organization.

  This command can fail for the following reasons:
      * There is no project with the given ID.
      * There is no organization with the given ID, if an organization is given
        as the destination.
      * There is no folder with the given ID, if a folder is given as the
        destination.
      * More than one of organization or folder is provided.
      * The new destination is not in the same organization as the project, if
        the project is already in an organization.
      * The active account does not have  the
        resourcemanager.projects.update permission for the given
        project.
      * The active account does not have  the
        resourcemanager.projects.create permission for the given
        organization.
      * The given project is already in an organization.

  ## EXAMPLES

  The following command moves a project with the ID `super-awesome-project` into
  the organization `25872158`:

    $ {command} super-awesome-project --organization=25872158
  """

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    project_flags.GetProjectFlag('move').AddToParser(parser)
    folder_flags.AddParentFlagsToParser(parser)

  def Format(self, args):
    return self.ListFormat(args)

  def Run(self, args):
    folder_flags.CheckParentFlags(args)
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Update(
        project_ref,
        parent=projects_api.ParentNameToResourceId(
            folder_flags.GetParentFromFlags(args)))
    log.UpdatedResource(project_ref)
    return result
