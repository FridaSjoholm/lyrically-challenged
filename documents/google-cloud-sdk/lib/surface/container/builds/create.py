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
"""Create build command."""

from googlecloudsdk.calliope import base
# Importing the beta version of this command to reduce repetition.
from surface.container.builds import submit


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(submit.Submit):
  """Create a build using the Google Container Builder service."""
