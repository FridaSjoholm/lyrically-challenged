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
"""Flags and helpers for the compute target-pools commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags


def TargetPoolArgument(required=True, help_suffix='.'):
  return compute_flags.ResourceArgument(
      resource_name='target pool',
      completion_resource_id='compute.targetPools',
      plural=False,
      required=required,
      regional_collection='compute.targetPools',
      short_help='The name of the target pool{0}'.format(help_suffix),
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def BackupPoolArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backup pool',
      name='--backup-pool',
      completion_resource_id='compute.targetPools',
      plural=False,
      required=required,
      regional_collection='compute.targetPools')


def TargetPoolArgumentForAddRemoveInstances(required=True, help_suffix='.'):
  return compute_flags.ResourceArgument(
      resource_name='target pool',
      completion_resource_id='compute.targetPools',
      plural=False,
      required=required,
      regional_collection='compute.targetPools',
      short_help='The name of the target pool{0}'.format(help_suffix),
      region_explanation=('If not specified it will be set the'
                          ' region of the instances.'))
