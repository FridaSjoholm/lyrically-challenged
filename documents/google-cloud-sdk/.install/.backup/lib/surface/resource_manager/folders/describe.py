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
"""Command to show metadata for a specified folder."""

import textwrap

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.command_lib.resource_manager import folders_base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(folders_base.FolderCommand, base.DescribeCommand):
  """Show metadata for a folder.

  Shows metadata for a folder, given a valid folder ID.

  This command can fail for the following reasons:
      * The folder specified does not exist.
      * The active account does not have permission to access the given
        folder.
  """
  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          The following command prints metadata for a folder with the
          ID `3589215982`:

            $ {command} 3589215982
    """),
  }

  @staticmethod
  def Args(parser):
    flags.FolderIdArg('you want to describe.').AddToParser(parser)

  def Run(self, args):
    return folders.GetFolder(args.id)
