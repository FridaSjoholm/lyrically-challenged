# Copyright 2017 Google Inc. All Rights Reserved.
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
"""List KeyRings within a Location."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import resources


class List(base.ListCommand):
  """List KeyRings within a Location.

  Lists all KeyRings within the given Location.

  ## EXAMPLES

  The following command lists a maximum of five KeyRings in the Location
  `global`:

    $ {command} --location global --limit=5
  """

  def Collection(self):
    return flags.KEY_RING_COLLECTION

  def GetUriFunc(self):
    return cloudkms_base.MakeGetUriFunc(self)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    location_ref = resources.REGISTRY.Create(flags.LOCATION_COLLECTION)

    request = messages.CloudkmsProjectsLocationsKeyRingsListRequest(
        projectsId=location_ref.projectsId,
        locationsId=location_ref.locationsId)

    return list_pager.YieldFromList(
        client.projects_locations_keyRings,
        request,
        field='keyRings',
        limit=args.limit,
        batch_size_attribute='pageSize')
