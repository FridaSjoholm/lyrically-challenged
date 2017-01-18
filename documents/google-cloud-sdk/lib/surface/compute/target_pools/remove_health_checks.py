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

"""Command for removing health checks from target pools."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.http_health_checks import (
    flags as http_health_check_flags)
from googlecloudsdk.command_lib.compute.target_pools import flags


class RemoveHealthChecks(base_classes.NoOutputAsyncMutator):
  """Remove an HTTP health check from a target pool.

  *{command}* is used to remove an HTTP health check
  from a target pool. Health checks are used to determine
  the health status of instances in the target pool. For more
  information on health checks and load balancing, see
  [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
  """

  HEALTH_CHECK_ARG = None
  TARGET_POOL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HEALTH_CHECK_ARG = (
        http_health_check_flags.HttpHealthCheckArgumentForTargetPool(
            'remove from'))
    cls.HEALTH_CHECK_ARG.AddArgument(parser)
    cls.TARGET_POOL_ARG = flags.TargetPoolArgument(
        help_suffix=' from which to remove the health check.')
    cls.TARGET_POOL_ARG.AddArgument(
        parser, operation_type='remove health checks from')

  @property
  def service(self):
    return self.compute.targetPools

  @property
  def method(self):
    return 'RemoveHealthCheck'

  @property
  def resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    http_health_check_ref = self.HEALTH_CHECK_ARG.ResolveAsResource(
        args, self.resources)

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    request = self.messages.ComputeTargetPoolsRemoveHealthCheckRequest(
        region=target_pool_ref.region,
        project=self.project,
        targetPool=target_pool_ref.Name(),
        targetPoolsRemoveHealthCheckRequest=(
            self.messages.TargetPoolsRemoveHealthCheckRequest(
                healthChecks=[self.messages.HealthCheckReference(
                    healthCheck=http_health_check_ref.SelfLink())])))

    return [request]
