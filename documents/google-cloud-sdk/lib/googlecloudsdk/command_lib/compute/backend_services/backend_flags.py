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

"""Flags and helpers for the compute backend-services backend commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import log


def AddDescription(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend.')


def AddInstanceGroup(parser, operation_type, with_deprecated_zone=False):
  """Add arguments to define instance group."""
  parser.add_argument(
      '--instance-group',
      required=True,
      help='The name or URI of a Google Cloud Instance Group.')

  scope_parser = parser.add_mutually_exclusive_group()
  flags.AddRegionFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
  if with_deprecated_zone:
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='{0} the backend service'.format(operation_type),
        explanation='DEPRECATED, use --instance-group-zone flag instead.')
  flags.AddZoneFlag(
      scope_parser,
      resource_type='instance group',
      operation_type='{0} the backend service'.format(operation_type),
      flag_prefix='instance-group',
      explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)


def WarnOnDeprecatedFlags(args):
  if getattr(args, 'zone', None):  # TODO(b/28518663).
    log.warn('The --zone flag is deprecated, please use --instance-group-zone'
             ' instead. It will be removed in a future release.')


def _GetBalancingModes():
  """Returns the --balancing-modes flag value choices name:description dict."""
  balancing_modes = {
      'RATE': """\
          Spreads load based on how many requests per second (RPS) the group
          can handle. There are two ways to specify max RPS: *--max-rate* which
          defines the max RPS for the whole group or *--max-rate-per-instance*,
          which defines the max RPS on a per-instance basis.
          """,
      'UTILIZATION': """\
          Relies on the CPU utilization of the instances in the group when
          balancing load. Use *--max-utilization* to set a maximum target CPU
          utilization for each instance. Use *--max-rate-per-instance* or
          *--max-rate* to optionally limit based on RPS in addition to CPU.
          You can optionally also limit based on connections (for TCP/SSL) in
          addition to CPU by setting *--max-connections* or
          *--max-connections-per-instance*.
          """,
      'CONNECTION': """\
          Spreads load based on how many concurrent connections the group
          can handle. There are two ways to specify max connections:
          *--max-connections* which defines the max number of connections
          for the whole group or *--max-connections-per-instance*, which
          defines the max number of connections on a per-instance basis.
          """,
  }
  return balancing_modes


def AddBalancingMode(parser):
  """Add balancing mode arguments."""
  balancing_mode = parser.add_argument(
      '--balancing-mode',
      choices=_GetBalancingModes(),
      type=lambda x: x.upper(),
      help='Defines the strategy for balancing load.')
  balancing_mode.detailed_help = """\
    Defines the strategy for balancing load.

    *RATE* and the max rate arguments are available only
    in backend services with HTTP based protocols.

    For backend services with TCP/SSL protocol either *UTILIZATION* or
    *CONNECTION* are available.

      """


def AddMaxUtilization(parser):
  max_utilization = parser.add_argument(
      '--max-utilization',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help=('The target CPU utilization of the group as a '
            'float in the range [0.0, 1.0].'))
  max_utilization.detailed_help = """\
      The target CPU utilization for the group as a float in the range
      [0.0, 1.0]. This flag can only be provided when the balancing
      mode is *UTILIZATION*.
      """


def AddCapacityLimits(parser):
  """Add capacity thresholds arguments."""
  AddMaxUtilization(parser)
  capacity_group = parser.add_mutually_exclusive_group()

  capacity_group.add_argument(
      '--max-rate',
      type=int,
      help='Maximum requests per second (RPS) that the group can handle.')

  capacity_group.add_argument(
      '--max-rate-per-instance',
      type=float,
      help='The maximum per-instance requests per second (RPS).')

  capacity_group.add_argument(
      '--max-connections',
      type=int,
      help='Maximum concurrent connections that the group can handle.')

  capacity_group.add_argument(
      '--max-connections-per-instance',
      type=int,
      help='The maximum concurrent connections per-instance.')


def AddCapacityScalar(parser):
  capacity_scaler = parser.add_argument(
      '--capacity-scaler',
      type=arg_parsers.BoundedFloat(lower_bound=0.0, upper_bound=1.0),
      help=('A float in the range [0.0, 1.0] that scales the maximum '
            'parameters for the group (e.g., max rate). The default is 1.0.'))
  capacity_scaler.detailed_help = """\
      A float in the range [0.0, 1.0] that scales the maximum
      parameters for the group (e.g., max rate). A value of 0.0 will
      cause no requests to be sent to the group (i.e., it adds the
      group in a ``drained'' state).
      """
