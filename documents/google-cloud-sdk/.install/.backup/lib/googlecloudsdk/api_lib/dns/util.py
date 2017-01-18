# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Common utility functions for the dns tool."""

from googlecloudsdk.calliope import base


def AppendTrailingDot(name):
  return name if not name or name.endswith('.') else name + '.'


ZONE_FLAG = base.Argument(
    '--zone',
    '-z',
    completion_resource='dns.managedZones',
    help='Name of the managed-zone whose record-sets you want to manage.',
    required=True)
