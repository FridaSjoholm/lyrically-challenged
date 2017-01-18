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
"""The command group for CryptoKeys."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


class CryptoKeys(base.Group):
  """Create and manage CryptoKeys.

  A CryptoKey represents a logical key that can be used for cryptographic
  operations.
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingFlag(parser)
    flags.AddLocationFlag(parser)

  def Filter(self, context, args):
    resources.REGISTRY.SetParamDefault(
        'cloudkms', None, 'locationsId',
        resolvers.FromArgument('--location', args.location))
    resources.REGISTRY.SetParamDefault(
        'cloudkms', None, 'keyRingsId',
        resolvers.FromArgument('--keyring', args.keyring))
