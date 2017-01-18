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
"""Fetch the IAM policy for a KeyRing."""

from googlecloudsdk.api_lib.cloudkms import iam
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class GetIamPolicy(base.Command):
  """Get the IAM policy for a KeyRing.

  Gets the IAM policy for the given KeyRing.

  Returns an empty policy if the resource does not have a policy set.

  ## EXAMPLES

  The following command gets the IAM policy for the KeyRing `fellowship`
  within the location `us-central1`:

    $ {command} fellowship --location us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingArgument(parser, 'whose IAM policy to fetch')

  def Run(self, args):
    return iam.GetKeyRingIamPolicy(flags.ParseKeyRingName(args))
