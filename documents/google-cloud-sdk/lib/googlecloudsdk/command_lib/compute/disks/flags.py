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

"""Flags and helpers for the compute disks commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags

_DETAILED_SOURCE_SNAPSHOT_HELP = """\
      A source snapshot used to create the disks. It is safe to
      delete a snapshot after a disk has been created from the
      snapshot. In such cases, the disks will no longer reference
      the deleted snapshot. To get a list of snapshots in your
      current project, run `gcloud compute snapshots list`. A
      snapshot from an existing disk can be created using the
      `gcloud compute disks snapshot` command. This flag is mutually
      exclusive with *--image*.

      When using this option, the size of the disks must be at least
      as large as the snapshot size. Use *--size* to adjust the
      size of the disks.
"""

DISK_ARG = compute_flags.ResourceArgument(
    resource_name='disk',
    completion_resource_id='compute.disks',
    name='DISK_NAME',
    zonal_collection='compute.disks',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)

DISKS_ARG = compute_flags.ResourceArgument(
    resource_name='disk',
    completion_resource_id='compute.disks',
    plural=True,
    name='DISK_NAME',
    zonal_collection='compute.disks',
    zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)

SOURCE_SNAPSHOT_ARG = compute_flags.ResourceArgument(
    resource_name='snapshot',
    completion_resource_id='compute.snapshots',
    name='--source-snapshot',
    plural=False,
    required=False,
    global_collection='compute.snapshots',
    short_help='A source snapshot used to create the disks.',
    detailed_help=_DETAILED_SOURCE_SNAPSHOT_HELP,)
