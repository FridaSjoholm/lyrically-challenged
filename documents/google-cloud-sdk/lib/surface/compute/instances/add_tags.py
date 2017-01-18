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
"""Command for adding tags to instances."""
import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers


class InstancesAddTags(base_classes.InstanceTagsMutatorMixin,
                       base_classes.ReadWriteCommand):
  """Add tags to Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    base_classes.InstanceTagsMutatorMixin.Args(parser)
    tags = parser.add_argument(
        '--tags',
        required=True,
        type=arg_parsers.ArgList(min_length=1),
        help='A list of tags to attach to the instance.',
        metavar='TAG')
    tags.detailed_help = """\
        Specifies strings to be attached to the instance for later
        identifying the instance when adding network firewall rules.
        Multiple tags can be attached by repeating this flag.
        """

  def Modify(self, args, existing):
    new_object = copy.deepcopy(existing)

    # Do not re-order the items if the object won't change, or the objects
    # will not be considered equal and an unnecessary API call will be made.
    new_tags = set(new_object.tags.items + args.tags)
    if new_tags != set(new_object.tags.items):
      new_object.tags.items = sorted(new_tags)

    return new_object


InstancesAddTags.detailed_help = {
    'brief': 'Add tags to Google Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* is used to add tags to Google Compute Engine virtual
        machine instances. For example, running:

          $ {command} example-instance --tags tag-1,tag-2

        will add tags ``tag-1'' and ``tag-2'' to 'example-instance'.

        Tags can be used to identify the instances when adding network
        firewall rules. Tags can also be used to get firewall rules that
        already exist to be applied to the instance. See
        gcloud_compute_firewall-rules_create(1) for more details.
        """,
}
