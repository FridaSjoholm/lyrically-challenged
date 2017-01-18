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

"""List command for gcloud debug snapshots command group."""

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Describe(base.DescribeCommand):
  """Describe debug snapshots."""

  detailed_help = {
      'DESCRIPTION': """\
          This command describes debug snapshots for a Cloud Debugger debug
          target. If the snapshot has been completed, the output will include
          details on the stack trace and local variables, stored in a compact
          form which is primarily intended to be machine-readable rather than
          human-readable.
      """
  }

  @staticmethod
  def Args(parser):
    debug.AddIdOptions(parser, 'snapshot', 'snapshots', 'displayed')

  def Run(self, args):
    """Run the describe command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    self.user_email = properties.VALUES.core.account.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    return debuggee.ListBreakpoints(args.location,
                                    resource_ids=args.ids,
                                    restrict_to_type=debugger.SNAPSHOT_TYPE)

  def Collection(self):
    return 'debug.snapshots'
