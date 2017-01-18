# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for setting whether to auto-delete a disk."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


class SetDiskAutoDelete(base_classes.ReadWriteCommand):
  """Set auto-delete behavior for disks."""

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)

    parser.add_argument(
        '--auto-delete',
        action='store_true',
        default=True,
        help='Enables auto-delete for the given disk.')

    disk_group = parser.add_mutually_exclusive_group(required=True)

    disk = disk_group.add_argument(
        '--disk',
        help=('Specify a disk to set auto-delete for by persistent disk '
              'name.'))
    disk.detailed_help = """\
        Specifies a disk to set auto-delete for by its resource name. If
        you specify a disk to set auto-delete for by persistent disk name,
        then you must not specify its device name using the
        ``--device-name'' flag.
        """

    device_name = disk_group.add_argument(
        '--device-name',
        help=('Specify a disk to set auto-delete for by the name the '
              'guest operating system sees.'))
    device_name.detailed_help = """\
        Specifies a disk to set auto-delete for by its device name,
        which is the name that the guest operating system sees. The
        device name is set at the time that the disk is attached to the
        instance, and need not be the same as the persistent disk name.
        If the disk's device name is specified, then its persistent disk
        name must not be specified using the ``--disk'' flag.
        """

  @property
  def service(self):
    return self.compute.instances

  @property
  def resource_type(self):
    return 'instances'

  def CreateReference(self, args):
    return instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeInstancesGetRequest(
                instance=self.ref.Name(),
                project=self.project,
                zone=self.ref.zone))

  def GetSetRequest(self, args, replacement, existing):
    # Our protocol buffers are mutable, so they cannot be
    # hashed. Because of this, we cannot do a set subraction on the
    # lists of disks. Instead, the task of finding the changed disk is
    # relegated to a for-loop.
    for existing_disk, replacement_disk in zip(
        existing.disks, replacement.disks):
      if existing_disk != replacement_disk:
        changed_disk = replacement_disk

    return (self.service,
            'SetDiskAutoDelete',
            self.messages.ComputeInstancesSetDiskAutoDeleteRequest(
                deviceName=changed_disk.deviceName,
                instance=self.ref.Name(),
                project=self.project,
                zone=self.ref.zone,
                autoDelete=changed_disk.autoDelete))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)
    disk_found = False

    if args.disk:
      disk_ref = self.resources.Parse(
          args.disk, collection='compute.disks',
          params={'zone': self.ref.zone})

      for disk in replacement.disks:
        if disk.source == disk_ref.SelfLink():
          disk.autoDelete = args.auto_delete
          disk_found = True

      if not disk_found:
        raise exceptions.ToolException(
            'Disk [{0}] is not attached to instance [{1}] in zone [{2}].'
            .format(disk_ref.Name(), self.ref.Name(), self.ref.zone))

    else:
      for disk in replacement.disks:
        if disk.deviceName == args.device_name:
          disk.autoDelete = args.auto_delete
          disk_found = True

      if not disk_found:
        raise exceptions.ToolException(
            'No disk with device name [{0}] is attached to instance [{1}] '
            'in zone [{2}].'
            .format(args.device_name, self.ref.Name(), self.ref.zone))

    return replacement


SetDiskAutoDelete.detailed_help = {
    'brief': 'Set auto-delete behavior for disks',
    'DESCRIPTION': """\
        *${command}* is used to configure the auto-delete behavior for disks
        attached to Google Compute Engine virtual machines. When
        auto-delete is on, the persistent disk is deleted when the
        instance it is attached to is deleted.
        """,
}
