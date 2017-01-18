# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for setting target pools of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser):
  """Add args."""
  parser.add_argument(
      '--target-pools',
      required=True,
      type=arg_parsers.ArgList(min_length=0),
      metavar='TARGET_POOL',
      help=('Compute Engine Target Pools to add the instances to. '
            'Target Pools must be specified by name or by URL. Example: '
            '--target-pool target-pool-1,target-pool-2.'))


class SetTargetPools(base_classes.BaseAsyncMutator):
  """Set target pools of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @property
  def method(self):
    return 'SetTargetPools'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(
        self.compute_client, self.project)
    group_ref = resource_arg.ResolveAsResource(
        args, self.resources, default_scope=default_scope,
        scope_lister=scope_lister)

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      region = utils.ZoneNameToRegionName(group_ref.zone)
    else:
      region = group_ref.region

    pool_refs = []
    for target_pool in args.target_pools:
      pool_refs.append(self.resources.Parse(
          target_pool, collection='compute.targetPools',
          params={'region': region}))
    pools = [pool_ref.SelfLink() for pool_ref in pool_refs]

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
              instanceGroupManager=group_ref.Name(),
              instanceGroupManagersSetTargetPoolsRequest=(
                  self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                      targetPools=pools,
                  )
              ),
              project=self.project,
              zone=group_ref.zone,)
      )
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
              instanceGroupManager=group_ref.Name(),
              regionInstanceGroupManagersSetTargetPoolsRequest=(
                  self.messages.
                  RegionInstanceGroupManagersSetTargetPoolsRequest(
                      targetPools=pools,
                  )
              ),
              project=self.project,
              region=group_ref.region,)
      )
    return [(service, self.method, request)]


SetTargetPools.detailed_help = {
    'brief': 'Set target pools of managed instance group.',
    'DESCRIPTION': """
        *{command}* sets the target pools for an existing managed instance group.
Instances that are part of the managed instance group will be added to the
target pool automatically.

Setting a new target pool won't apply to existing instances in the group unless
they are recreated using the recreate-instances command. But any new instances
created in the managed instance group will be added to all of the provided
target pools for load balancing purposes.
""",
}
