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
"""Describe a KeyRing."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class Describe(base.DescribeCommand):
  """Get metadata for a KeyRing.

  Returns metadata for the given KeyRing.

  ## EXAMPLES

  The following command returns the metadata for the KeyRing `towers`
  in the location `us-east1`:

    $ {command} towers --location us-east1
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingArgument(parser, 'to describe')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    key_ring_ref = flags.ParseKeyRingName(args)
    return client.projects_locations_keyRings.Get(
        messages.CloudkmsProjectsLocationsKeyRingsGetRequest(
            projectsId=key_ring_ref.projectsId,
            locationsId=key_ring_ref.locationsId,
            keyRingsId=key_ring_ref.keyRingsId))
