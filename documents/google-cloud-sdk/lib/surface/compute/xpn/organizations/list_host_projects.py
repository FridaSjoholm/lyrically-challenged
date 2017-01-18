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
"""The `gcloud compute xpn organizations list-host-projects` command."""
from googlecloudsdk.api_lib.compute import xpn_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.xpn import util as command_lib_util
from googlecloudsdk.command_lib.organizations import flags as organizations_flags
from googlecloudsdk.core import properties


class ListHostProjects(base.ListCommand):
  """List the projects in a given organization that are enabled as XPN hosts."""

  detailed_help = {
      'EXAMPLES': """
          To list the XPN host projects in the organization with ID 12345, run:

            $ {command} 12345
            NAME       CREATION_TIMESTAMP            XPN_PROJECT_STATUS
            xpn-host1  2000-01-01T12:00:00.00-00:00  HOST
            xpn-host2  2000-01-02T12:00:00.00-00:00  HOST
      """
  }

  @staticmethod
  def Args(parser):
    organizations_flags.IdArg(
        'whose XPN host projects to list.').AddToParser(parser)

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def Run(self, args):
    xpn_client = xpn_api.GetXpnClient()
    project = properties.VALUES.core.project.Get(required=True)
    organization_id = args.id
    return xpn_client.ListOrganizationHostProjects(
        project, organization_id=organization_id)
