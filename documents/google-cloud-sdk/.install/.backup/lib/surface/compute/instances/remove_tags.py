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
"""Command for removing tags from instances."""
import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers


class RemoveTags(base_classes.InstanceTagsMutatorMixin,
                 base_classes.ReadWriteCommand):
  """Remove tags from Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    tags_group = parser.add_mutually_exclusive_group(required=True)
    tags = tags_group.add_argument(
        '--tags',
        type=arg_parsers.ArgList(min_length=1),
        help='Tags to remove from the instance.',
        metavar='TAG')
    tags.detailed_help = """\
        Specifies strings to be removed from the instance tags.
        Multiple tags can be removed by repeating this flag.
        """
    tags_group.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='Remove all tags from the instance.')

    base_classes.InstanceTagsMutatorMixin.Args(parser)

  def Modify(self, args, existing):
    new_object = copy.deepcopy(existing)
    if args.all:
      new_object.tags.items = []
    else:
      new_object.tags.items = sorted(
          set(new_object.tags.items) - set(args.tags))
    return new_object


RemoveTags.detailed_help = {
    'brief': 'Remove tags from Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* is used to remove tags to Google Compute Engine virtual
        machine instances.  For example:

          $ {command} example-instance --tags tag-1,tag-2

        will remove tags ``tag-1'' and ``tag-2'' from the existing tags of
        'example-instance'.

        Tags can be used to identify instances when adding network
        firewall rules. Tags can also be used to get firewall rules that already
        exist to be applied to the instance. See
        gcloud_compute_firewall-rules_create(1) for more details.
        """,
}
