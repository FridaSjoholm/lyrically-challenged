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
"""Restore a CryptoKeyVersion."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class Restore(base.UpdateCommand):
  """Restore a CryptoKeyVersion scheduled for destruction.

  Restores the given CryptoKeyVersion that was scheduled to be destroyed.

  This moves the CryptoKeyVersion from Scheduled for destruction to Disabled.
  Only CryptoKeyVersions which are Scheduled for destruction can be Restored.

  ## EXAMPLES

  The following command restores version 9 of CryptoKey `frodo` within
  KeyRing `fellowship` and Location `us-east1` which was previously scheduled
  for destruction:

    $ {command} 9 --location us-east1 --keyring fellowship --cryptokey frodo
  """

  @staticmethod
  def Args(parser):
    flags.AddCryptoKeyVersionArgument(parser, 'to restore')

  def Run(self, args):
    # pylint: disable=line-too-long
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    version_ref = flags.ParseCryptoKeyVersionName(args)
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsRestoreRequest(
        projectsId=version_ref.projectsId,
        locationsId=version_ref.locationsId,
        keyRingsId=version_ref.keyRingsId,
        cryptoKeysId=version_ref.cryptoKeysId,
        cryptoKeyVersionsId=version_ref.cryptoKeyVersionsId)

    ckv = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    return ckv.Restore(req)
