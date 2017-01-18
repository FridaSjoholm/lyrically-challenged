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
"""Flags and helpers for the compute routers commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags


def RouterArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='router',
      completion_resource_id='compute.routers',
      plural=False,
      required=required,
      regional_collection='compute.routers',
      short_help='The name of the router.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def RouterArgumentForVpnTunnel(required=True):
  return compute_flags.ResourceArgument(
      resource_name='router',
      name='--router',
      completion_resource_id='compute.routers',
      plural=False,
      required=required,
      regional_collection='compute.routers',
      short_help='The Router to use for dynamic routing.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)
