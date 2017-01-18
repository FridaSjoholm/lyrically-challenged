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

"""Command for creating routes."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.routes import flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags as vpn_flags
from googlecloudsdk.core import properties


def _AddGaHops(next_hop_group):
  """Attach arguments for GA next-hops to the a parser group."""

  next_hop_instance = next_hop_group.add_argument(
      '--next-hop-instance',
      help=('Specifies the name of an instance that should handle traffic '
            'matching this route.'))
  next_hop_instance.detailed_help = """\
      Specifies the name of an instance that should handle traffic
      matching this route. When this flag is specified, the zone of
      the instance must be specified using
      ``--next-hop-instance-zone''.
      """

  next_hop_address = next_hop_group.add_argument(
      '--next-hop-address',
      help=('Specifies the IP address of an instance that should handle '
            'matching packets.'))
  next_hop_address.detailed_help = """\
      Specifies the IP address of an instance that should handle
      matching packets. The instance must have IP forwarding enabled
      (i.e., include ``--can-ip-forward'' when creating the instance
      using `gcloud compute instances create`)
      """

  next_hop_gateway = next_hop_group.add_argument(
      '--next-hop-gateway',
      help='Specifies the gateway that should handle matching packets.')
  next_hop_gateway.detailed_help = """\
      Specifies the gateway that should handle matching
      packets. Currently, the only acceptable value is
      ``default-internet-gateway'' which is a gateway operated by
      Google Compute Engine.
      """

  next_hop_group.add_argument(
      '--next-hop-vpn-tunnel',
      help=('The target VPN tunnel that will receive forwarded traffic.'))


def _Args(parser):
  """Add arguments for route creation."""

  parser.add_argument(
      '--description',
      help='An optional, textual description for the route.')

  parser.add_argument(
      '--network',
      default='default',
      help='Specifies the network to which the route will be applied.')

  tags = parser.add_argument(
      '--tags',
      type=arg_parsers.ArgList(min_length=1),
      default=[],
      metavar='TAG',
      help='Identifies the set of instances that this route will apply to.')
  tags.detailed_help = """\
      Identifies the set of instances that this route will apply to. If no
      tags are provided, the route will apply to all instances in the network.
      """

  destination_range = parser.add_argument(
      '--destination-range',
      required=True,
      help=('The destination range of outgoing packets that the route will '
            'apply to.'))
  destination_range.detailed_help = """\
      The destination range of outgoing packets that the route will
      apply to. To match all traffic, use ``0.0.0.0/0''.
      """

  priority = parser.add_argument(
      '--priority',
      default=1000,
      help=('Specifies the priority of this route relative to other routes '
            'with the same specificity.'),
      type=int)
  priority.detailed_help = """\
      Specifies the priority of this route relative to other routes
      with the same specificity. The lower the value, the higher the
      priority.
      """

  next_hop = parser.add_mutually_exclusive_group(required=True)

  _AddGaHops(next_hop)

  next_hop_instance_zone = parser.add_argument(
      '--next-hop-instance-zone',
      help='The zone of the next hop instance.',
      action=actions.StoreProperty(properties.VALUES.compute.zone))
  next_hop_instance_zone.detailed_help = ("""\
      The zone of the next hop instance.
      """ + compute_flags.ZONE_PROPERTY_EXPLANATION)

  next_hop_vpn_tunnel_region = parser.add_argument(
      '--next-hop-vpn-tunnel-region',
      help='The region of the next hop vpn tunnel.')
  next_hop_vpn_tunnel_region.detailed_help = ("""\
     The region of the next hop vpn tunnel.
     """ + compute_flags.REGION_PROPERTY_EXPLANATION)


def _CreateRequests(cmd, args):
  """Make API requests for route creation, callable from multiple tracks."""

  network_uri = cmd.NETWORK_ARG.ResolveAsResource(args,
                                                  cmd.resources).SelfLink()

  if args.next_hop_instance:
    next_hop_instance_uri = cmd.INSTANCE_ARG.ResolveAsResource(
        args,
        cmd.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(
            cmd.compute_client, cmd.project)).SelfLink()
  else:
    if args.next_hop_instance_zone:
      raise exceptions.ToolException(
          '[--next-hop-instance-zone] can only be specified in conjunction '
          'with [--next-hop-instance].')
    next_hop_instance_uri = None

  if args.next_hop_gateway:
    # TODO(b/18201355): This is hack.
    #
    # There is currently no "gateways" resource type in the Compute
    # API, however, the API does accept a "gateways" URI. We need to
    # extend the resources module to allow for arbitrary URI
    # patterns to be registered. With the logic below, a URI value
    # for --next-hop-gateway will not work.
    next_hop_gateway_uri = (
        cmd.compute.url +
        'projects/' + cmd.project +
        '/global/gateways/' + args.next_hop_gateway)
  else:
    next_hop_gateway_uri = None

  route_ref = cmd.ROUTE_ARG.ResolveAsResource(args, cmd.resources)

  next_hop_vpn_tunnel_uri = None

  if args.next_hop_vpn_tunnel:
    next_hop_vpn_tunnel_uri = cmd.VPN_TUNNEL_ARG.ResolveAsResource(
        args,
        cmd.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(
            cmd.compute_client, cmd.project)).SelfLink()
  elif args.next_hop_vpn_tunnel_region:
    raise exceptions.ToolException(
        '[--next-hop-vpn-tunnel-region] can only be specified in '
        'conjunction with [--next-hop-vpn-tunnel].')

  request = cmd.messages.ComputeRoutesInsertRequest(
      project=cmd.project,
      route=cmd.messages.Route(
          description=args.description,
          destRange=args.destination_range,
          name=route_ref.Name(),
          network=network_uri,
          nextHopInstance=next_hop_instance_uri,
          nextHopIp=args.next_hop_address,
          nextHopGateway=next_hop_gateway_uri,
          nextHopVpnTunnel=next_hop_vpn_tunnel_uri,
          priority=args.priority,
          tags=args.tags,
      ))
  return [request]


class Create(base_classes.BaseAsyncCreator):
  """Create a new route."""

  NETWORK_ARG = None
  INSTANCE_ARG = None
  VPN_TUNNEL_ARG = None
  ROUTE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'Specifies the network to which the route will be applied.',
        required=False)
    cls.INSTANCE_ARG = instance_flags.InstanceArgumentForRoute(required=False)
    cls.VPN_TUNNEL_ARG = vpn_flags.VpnTunnelArgumentForRoute(required=False)
    cls.ROUTE_ARG = flags.RouteArgument()
    cls.ROUTE_ARG.AddArgument(parser)
    _Args(parser)

  @property
  def service(self):
    return self.compute.routes

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'routes'

  def CreateRequests(self, args):
    return _CreateRequests(self, args)


Create.detailed_help = {
    'brief': 'Create a new route',
    'DESCRIPTION': """\
        *{command}* is used to create routes. A route is a rule that
        specifies how certain packets should be handled by the virtual
        network. Routes are associated with virtual machine instances
        by tag, and the set of routes for a particular VM is called
        its routing table. For each packet leaving a virtual machine,
        the system searches that machine's routing table for a single
        best matching route.

        Routes match packets by destination IP address, preferring
        smaller or more specific ranges over larger ones (see
        ``--destination-range''). If there is a tie, the system selects
        the route with the smallest priority value. If there is still
        a tie, it uses the layer three and four packet headers to
        select just one of the remaining matching routes. The packet
        is then forwarded as specified by ``--next-hop-address'',
        ``--next-hop-instance'', ``--next-hop-vpn-tunnel'', or
        ``--next-hop-gateway'' of the winning route. Packets that do
        not match any route in the sending virtual machine routing
        table will be dropped.

        Exactly one of ``--next-hop-address'', ``--next-hop-gateway'',
        ``--next-hop-vpn-tunnel'', or ``--next-hop-instance'' must be
        provided with this command.
        """,
    }
