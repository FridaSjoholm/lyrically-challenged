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
"""Create a KeyRing."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class Create(base.CreateCommand):
  """Create a new KeyRing.

  Creates a new KeyRing within the given Location.

  ## Examples

  The following command creates a KeyRing named `fellowship` within the
  Location `global`:

    $ {command} fellowship --location global
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingArgument(parser, 'to create')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    key_ring_ref = flags.ParseKeyRingName(args)

    req = messages.CloudkmsProjectsLocationsKeyRingsCreateRequest(
        projectsId=key_ring_ref.projectsId,
        locationsId=key_ring_ref.locationsId,
        keyRingId=key_ring_ref.keyRingsId)

    return client.projects_locations_keyRings.Create(req)
