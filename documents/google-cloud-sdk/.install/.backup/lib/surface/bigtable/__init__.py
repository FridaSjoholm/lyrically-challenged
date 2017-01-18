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
"""The main command group for bigtable."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BigtableV2(base.Group):
  """Manage your Cloud Bigtable storage."""

  def Filter(self, context, args):
    project = properties.VALUES.core.project
    resolver = resolvers.FromProperty(project)
    resources.REGISTRY.SetParamDefault(
        'bigtableadmin', collection=None, param='projectsId', resolver=resolver)
