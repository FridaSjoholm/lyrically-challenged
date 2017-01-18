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
"""Command for deleting instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.core.console import console_io

AUTO_DELETE_OVERRIDE_CHOICES = {
    'boot': 'The first partition is reserved for the root filesystem.',
    'data': 'A non-boot disk.',
    'all': 'All disk types.',
}


class Delete(base_classes.ZonalDeleter):
  """Delete Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    auto_delete_override = parser.add_mutually_exclusive_group()

    delete_disks = auto_delete_override.add_argument(
        '--delete-disks',
        choices=AUTO_DELETE_OVERRIDE_CHOICES,
        metavar='DISK-TYPE',
        help=('The types of disks to delete with instance deletion '
              "regardless of the disks' auto-delete configuration."))
    delete_disks.detailed_help = """\
        The types of disks to delete with instance deletion regardless
        of the disks' auto-delete configuration. When this flag is
        provided, the auto-delete bits on the attached disks are
        modified accordingly before the instance deletion requests are
        issued. For more information on disk auto-deletion, see
        [](https://cloud.google.com/compute/docs/disks/persistent-disks#updateautodelete)
        """

    keep_disks = auto_delete_override.add_argument(
        '--keep-disks',
        choices=AUTO_DELETE_OVERRIDE_CHOICES,
        metavar='DISK-TYPE',
        help=('The types of disks to not delete with instance deletion '
              "regardless of the disks' auto-delete configuration."))
    keep_disks.detailed_help = """\
        The types of disks to not delete with instance deletion regardless
        of the disks' auto-delete configuration. When this flag is
        provided, the auto-delete bits on the attached disks are
        modified accordingly before the instance deletion requests are
        issued. For more information on disk auto-deletion, see
        [](https://cloud.google.com/compute/docs/disks/persistent-disks#updateautodelete)
        """

    instance_flags.INSTANCES_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.instances

  @property
  def resource_type(self):
    return 'instances'

  def GetInstances(self, refs):
    """Fetches instance objects corresponding to the given references."""
    instance_get_requests = []
    for ref in refs:
      request_protobuf = self.messages.ComputeInstancesGetRequest(
          instance=ref.Name(),
          zone=ref.zone,
          project=ref.project)
      instance_get_requests.append((self.service, 'Get', request_protobuf))

    errors = []
    instances = list(request_helper.MakeRequests(
        requests=instance_get_requests,
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))
    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Failed to fetch some instances:')
    return instances

  def PromptIfDisksWithoutAutoDeleteWillBeDeleted(self, disks_to_warn_for):
    """Prompts if disks with False autoDelete will be deleted.

    Args:
      disks_to_warn_for: list of references to disk resources.
    """
    if not disks_to_warn_for:
      return

    prompt_list = []
    for ref in disks_to_warn_for:
      prompt_list.append('[{0}] in [{1}]'.format(ref.Name(), ref.zone))

    prompt_message = utils.ConstructList(
        'The following disks are not configured to be automatically deleted '
        'with instance deletion, but they will be deleted as a result of '
        'this operation if they are not attached to any other instances:',
        prompt_list)
    if not console_io.PromptContinue(message=prompt_message):
      raise exceptions.ToolException('Deletion aborted by user.')

  def AutoDeleteMustBeChanged(self, args, disk_resource):
    """Returns True if the autoDelete property of the disk must be changed."""
    if args.keep_disks == 'boot':
      return disk_resource.autoDelete and disk_resource.boot
    elif args.keep_disks == 'data':
      return disk_resource.autoDelete and not disk_resource.boot
    elif args.keep_disks == 'all':
      return disk_resource.autoDelete

    elif args.delete_disks == 'data':
      return not disk_resource.autoDelete and not disk_resource.boot
    elif args.delete_disks == 'all':
      return not disk_resource.autoDelete
    elif args.delete_disks == 'boot':
      return not disk_resource.autoDelete and disk_resource.boot

    return False

  def CreateRequests(self, args):
    refs = instance_flags.INSTANCES_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    utils.PromptForDeletion(
        refs,
        scope_name='zone',
        prompt_title=('The following instances will be deleted. Attached '
                      'disks configured to be auto-deleted will be deleted '
                      'unless they are attached to any other instances. '
                      'Deleting a disk is irreversible and any data on the '
                      'disk will be lost.'))

    if args.delete_disks or args.keep_disks:
      instance_resources = self.GetInstances(refs)

      disks_to_warn_for = []
      set_auto_delete_requests = []

      for ref, resource in zip(refs, instance_resources):
        for disk in resource.disks:
          # Determines whether the current disk needs to have its
          # autoDelete parameter changed.
          if not self.AutoDeleteMustBeChanged(args, disk):
            continue

          # At this point, we know that the autoDelete property of the
          # disk must be changed. Since autoDelete is a boolean, we
          # just negate it!
          # Yay, computer science! :) :) :)
          new_auto_delete = not disk.autoDelete
          if new_auto_delete:
            disks_to_warn_for.append(self.resources.Parse(
                disk.source, collection='compute.disks',
                params={'zone': ref.zone}))

          set_auto_delete_requests.append((
              self.service,
              'SetDiskAutoDelete',
              self.messages.ComputeInstancesSetDiskAutoDeleteRequest(
                  autoDelete=new_auto_delete,
                  deviceName=disk.deviceName,
                  instance=ref.Name(),
                  project=ref.project,
                  zone=ref.zone)))

      if set_auto_delete_requests:
        self.PromptIfDisksWithoutAutoDeleteWillBeDeleted(disks_to_warn_for)
        errors = []
        list(request_helper.MakeRequests(
            requests=set_auto_delete_requests,
            http=self.http,
            batch_url=self.batch_url,
            errors=errors,
            custom_get_requests=None))
        if errors:
          utils.RaiseToolException(
              errors,
              error_message=('Some requests to change disk auto-delete '
                             'behavior failed:'))

    delete_requests = []
    for ref in refs:
      request_protobuf = self.messages.ComputeInstancesDeleteRequest(
          instance=ref.Name(),
          zone=ref.zone,
          project=ref.project)
      delete_requests.append(request_protobuf)

    return delete_requests

  def Format(self, _):
    return 'none'


Delete.detailed_help = {
    'brief': 'Delete Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine virtual machine
        instances.
        """,
}
