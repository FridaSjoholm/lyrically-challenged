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
"""Command for creating target VPN Gateways."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.target_vpn_gateways import flags


class Create(base_classes.BaseAsyncCreator):
  """Create a VPN Gateway."""

  # Placeholder to indicate that a detailed_help field exists and should
  # be set outside the class definition.
  detailed_help = None

  NETWORK_ARG = None
  TARGET_VPN_GATEWAY_ARG = None

  @classmethod
  def Args(cls, parser):
    """Adds arguments to the supplied parser."""
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'A reference to a network in this project',
        detailed_help="""\
        A reference to a network in this project to
        contain the VPN Gateway.
        """)
    cls.NETWORK_ARG.AddArgument(parser)
    cls.TARGET_VPN_GATEWAY_ARG = flags.TargetVpnGatewayArgument()
    cls.TARGET_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='create')

    parser.add_argument(
        '--description',
        help='An optional, textual description for the target VPN Gateway.')

  @property
  def service(self):
    return self.compute.targetVpnGateways

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'targetVpnGateways'

  def CreateRequests(self, args):
    """Builds API requests to construct Target VPN Gateways.

    Args:
      args: argparse.Namespace, The arguments received by this command.

    Returns:
      [protorpc.messages.Message], A list of requests to be executed
      by the compute API.
    """

    target_vpn_gateway_ref = self.TARGET_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))
    network_ref = self.NETWORK_ARG.ResolveAsResource(args, self.resources)

    request = self.messages.ComputeTargetVpnGatewaysInsertRequest(
        project=self.project,
        region=target_vpn_gateway_ref.region,
        targetVpnGateway=self.messages.TargetVpnGateway(
            description=args.description,
            name=target_vpn_gateway_ref.Name(),
            network=network_ref.SelfLink()
            ))
    return [request]

Create.detailed_help = {
    'brief': 'Create a target VPN Gateway',
    'DESCRIPTION': """
        *{command}* is used to create a target VPN Gateway. A target VPN
        Gateway can reference one or more VPN tunnels that connect it to
        external VPN gateways. A VPN Gateway may also be referenced by
        one or more forwarding rules that define which packets the
        gateway is responsible for routing.
        """
    }
