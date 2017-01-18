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
"""Command for adding instances to target pools."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.target_pools import flags
from googlecloudsdk.core import log


class AddInstances(base_classes.NoOutputAsyncMutator):
  """Add instances to a target pool."""

  INSTANCE_ARG = None
  TARGET_POOL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INSTANCE_ARG = instance_flags.InstanceArgumentForTargetPool('add to')
    cls.INSTANCE_ARG.AddArgument(
        parser,
        operation_type='add to the target pool',
        cust_metavar='INSTANCE')
    cls.TARGET_POOL_ARG = flags.TargetPoolArgumentForAddRemoveInstances(
        help_suffix=' to which to add the instances.')
    cls.TARGET_POOL_ARG.AddArgument(parser)

    compute_flags.AddZoneFlag(
        parser,
        resource_type='instances',
        operation_type='add to the target pool',
        explanation=(
            'DEPRECATED, use --instances-zone. '
            'If not specified, you will be prompted to select a zone.'))

  @property
  def service(self):
    return self.compute.targetPools

  @property
  def method(self):
    return 'AddInstance'

  @property
  def resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    if args.zone and not args.instances_zone:
      args.instances_zone = args.zone
      log.warn('The --zone flag is deprecated. Use equivalent '
               '--instances-zone=%s flag.', args.instances_zone)

    instance_refs = self.INSTANCE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    instances = [
        self.messages.InstanceReference(instance=instance_ref.SelfLink())
        for instance_ref in instance_refs]

    unique_regions = set(utils.ZoneNameToRegionName(instance_ref.zone)
                         for instance_ref in instance_refs)

    # Check that all regions are the same.
    if len(unique_regions) > 1:
      raise calliope_exceptions.ToolException(
          'Instances must all be in the same region as the target pool.')

    region = unique_regions.pop()

    # Check that the region of the instances is the same as target pool region.
    if args.region and region != args.region:
      raise calliope_exceptions.ToolException(
          'Instances must all be in the same region as the target pool.')

    args.region = region

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(args,
                                                             self.resources)

    request = self.messages.ComputeTargetPoolsAddInstanceRequest(
        region=target_pool_ref.region,
        project=self.project,
        targetPool=target_pool_ref.Name(),
        targetPoolsAddInstanceRequest=(
            self.messages.TargetPoolsAddInstanceRequest(instances=instances)))
    return [request]


AddInstances.detailed_help = {
    'brief': 'Add instances to a target pool',
    'DESCRIPTION': """\
        *{command}* is used to add one or more instances to a target pool.
        For more information on health checks and load balancing, see
        [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
        """,
}
