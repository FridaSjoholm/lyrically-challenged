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
"""Command for listing health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


class _BaseList(object):
  """List health checks."""

  @staticmethod
  def Args(parser):
    base_classes.BaseLister.Args(parser)

    protocol = parser.add_argument(
        '--protocol',
        help='The health check protocol to be listed. Default is all listed.')
    protocol.detailed_help = """\
        If protocol is specified, only health checks for that protocol are
        listed, and protocol-specific columns are added to the output. By
        default, health checks for all protocols are listed.
        """

  def _ConvertProtocolArgToValue(self, args):
    # Get the dictionary that maps strings to numbers, e.g. "HTTP" to 0.
    protocol_dict = self.messages.HealthCheck.TypeValueValuesEnum.to_dict()
    return protocol_dict.get(args.protocol.upper())

  def _ProtocolWhitelist(self):
    # Returns a list of whitelisted protocols.
    return [
        self.messages.HealthCheck.TypeValueValuesEnum.HTTP.number,
        self.messages.HealthCheck.TypeValueValuesEnum.HTTPS.number,
        self.messages.HealthCheck.TypeValueValuesEnum.TCP.number,
        self.messages.HealthCheck.TypeValueValuesEnum.SSL.number
    ]

  def _GetValidColumns(self, args):
    """Returns a list of valid columns."""
    # Start with the columns that apply to all protocols.
    columns = ['name:label=NAME', 'type:label=PROTOCOL']

    # Add protocol-specific columns. Note that we only need to worry about
    # protocols that were whitelisted in our GetResources method below.
    if args.protocol is not None:
      protocol_value = self._ConvertProtocolArgToValue(args)
      if (protocol_value ==
          self.messages.HealthCheck.TypeValueValuesEnum.HTTP.number):
        columns.extend(['httpHealthCheck.host:label=HOST',
                        'httpHealthCheck.port:label=PORT',
                        'httpHealthCheck.requestPath:label=REQUEST_PATH',
                        'httpHealthCheck.proxyHeader:label=PROXY_HEADER'])
      elif (protocol_value ==
            self.messages.HealthCheck.TypeValueValuesEnum.HTTPS.number):
        columns.extend(['httpsHealthCheck.host:label=HOST',
                        'httpsHealthCheck.port:label=PORT',
                        'httpsHealthCheck.requestPath:label=REQUEST_PATH',
                        'httpsHealthCheck.proxyHeader:label=PROXY_HEADER'])
      elif (protocol_value ==
            self.messages.HealthCheck.TypeValueValuesEnum.TCP.number):
        columns.extend(['tcpHealthCheck.port:label=PORT',
                        'tcpHealthCheck.request:label=REQUEST',
                        'tcpHealthCheck.response:label=RESPONSE',
                        'tcpHealthCheck.proxyHeader:label=PROXY_HEADER'])
      elif (protocol_value ==
            self.messages.HealthCheck.TypeValueValuesEnum.SSL.number):
        columns.extend(['sslHealthCheck.port:label=PORT',
                        'sslHealthCheck.request:label=REQUEST',
                        'sslHealthCheck.response:label=RESPONSE',
                        'sslHealthCheck.proxyHeader:label=PROXY_HEADER'])

    return columns

  def Format(self, args):
    columns = self._GetValidColumns(args)
    return 'table[]({columns})'.format(columns=','.join(columns))

  @property
  def service(self):
    return self.compute.healthChecks

  @property
  def resource_type(self):
    return 'healthChecks'

  def GetResources(self, args, errors):
    """Gets a list of global healthcheck resources."""
    health_checks = lister.GetGlobalResources(
        service=self.service,
        project=self.project,
        filter_expr=self.GetFilterExpr(args),
        http=self.http,
        batch_url=self.batch_url,
        errors=errors)

    # If a protocol is specified, check that it is one we support, and convert
    # it to a number.
    protocol_value = None
    if args.protocol is not None:
      protocol_value = self._ConvertProtocolArgToValue(args)
      if protocol_value not in self._ProtocolWhitelist():
        raise exceptions.ToolException(
            'Invalid health check protocol ' + args.protocol + '.')

    for health_check in health_checks:
      if protocol_value is None or health_check.type.number == protocol_value:
        yield health_check


_BaseList.detailed_help = base_classes.GetGlobalListerHelp('health checks')


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class ListBetaAndGA(_BaseList, base_classes.BaseLister):
  """List health checks in Beta or GA."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(_BaseList, base_classes.BaseLister):
  """List health checks in Alpha."""

  def _ProtocolWhitelist(self):
    # Returns a list of whitelisted protocols.
    whitelist = super(ListAlpha, self)._ProtocolWhitelist()
    whitelist.append(self.messages.HealthCheck.TypeValueValuesEnum.HTTP2.number)
    whitelist.append(self.messages.HealthCheck.TypeValueValuesEnum.UDP.number)
    return whitelist

  def Format(self, args):
    columns = self._GetValidColumns(args)
    if args.protocol is not None:
      protocol_value = self._ConvertProtocolArgToValue(args)
      if (protocol_value ==
          self.messages.HealthCheck.TypeValueValuesEnum.HTTP2.number):
        columns.extend(['http2HealthCheck.host:label=HOST',
                        'http2HealthCheck.port:label=PORT',
                        'http2HealthCheck.requestPath:label=REQUEST_PATH',
                        'http2HealthCheck.proxyHeader:label=PROXY_HEADER'])
      elif (protocol_value ==
            self.messages.HealthCheck.TypeValueValuesEnum.UDP.number):
        columns.extend(['udpHealthCheck.port:label=PORT',
                        'udpHealthCheck.request:label=REQUEST',
                        'udpHealthCheck.response:label=RESPONSE'])
    return 'table[]({columns})'.format(columns=','.join(columns))
