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
"""Command for creating sole tenant hosts."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope
from googlecloudsdk.command_lib.compute.sole_tenant_hosts import flags as hosts_flags


class Create(base_classes.BaseAsyncCreator):
  """Create Google Compute Engine sole tenant hosts."""

  @staticmethod
  def Args(parser):
    hosts_flags.HOSTS_ARG.AddArgument(parser)
    parser.add_argument(
        '--description',
        help='Specifies a textual description of the hosts.')
    parser.add_argument(
        '--host-type',
        help=('Specifies a type of the hosts. Type of a host determines '
              'resources available to instances running on it.'))

  @property
  def service(self):
    return self.compute.hosts

  @property
  def method(self):
    return 'Insert'

  def _CreateRequest(self, host_ref, description, host_type):
    return self.messages.ComputeHostsInsertRequest(
        host=self.messages.Host(
            name=host_ref.Name(),
            description=description,
            hostType=host_type),
        project=host_ref.project,
        zone=host_ref.zone)

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding hosts."""

    host_refs = hosts_flags.HOSTS_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=scope.ScopeEnum.ZONE,
        scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    host_properties = {
        'description': args.description,
        # TODO(user): Parse resource and pass full URL of host type once
        # the host type resource can be made visible (adding host type resource
        # is tracked in b/30067150).
        'host_type': args.host_type
    }
    return [self._CreateRequest(ref, **host_properties) for ref in host_refs]
