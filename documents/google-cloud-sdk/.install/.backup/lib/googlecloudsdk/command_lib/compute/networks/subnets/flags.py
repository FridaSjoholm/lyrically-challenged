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

"""Flags and helpers for the compute subnetworks commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope


def SubnetworkArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='subnetwork',
      completion_resource_id='compute.subnetworks',
      plural=False,
      required=required,
      regional_collection='compute.subnetworks',
      short_help='The name of the subnetwork.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def SubnetworkResolver():
  return compute_flags.ResourceResolver.FromMap(
      'subnetwork', {compute_scope.ScopeEnum.REGION: 'compute.subnetworks'})
