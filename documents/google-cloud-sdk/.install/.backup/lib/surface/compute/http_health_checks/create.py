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
"""Command for creating HTTP health checks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.http_health_checks import flags


class Create(base_classes.BaseAsyncCreator):
  """Create an HTTP health check to monitor load balanced instances."""

  HTTP_HEALTH_CHECKS_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HTTP_HEALTH_CHECKS_ARG = flags.HttpHealthCheckArgument()
    cls.HTTP_HEALTH_CHECKS_ARG.AddArgument(parser)

    host = parser.add_argument(
        '--host',
        help='The value of the host header used by the HTTP health check.')
    host.detailed_help = """\
        The value of the host header used in this HTTP health check request.
        By default, this is empty and Google Compute Engine automatically sets
        the host header in health requests to the same external IP address as
        the forwarding rule associated with the target pool.
        """

    port = parser.add_argument(
        '--port',
        help='The TCP port number for the health request. Default is 80.',
        type=int,
        default=80)
    port.detailed_help = """\
        The TCP port number that this health check monitors. The default value
        is 80.
        """

    request_path = parser.add_argument(
        '--request-path',
        help="The request path for the health check. Default is ``/''.",
        default='/')
    request_path.detailed_help = """\
        The request path that this health check monitors. For example,
        ``/healthcheck''. The default value is ``/''.
        """

    check_interval_sec = parser.add_argument(
        '--check-interval',
        help='How often to run the check. Default is 5s.',
        type=arg_parsers.Duration(),
        default='5s')
    check_interval_sec.detailed_help = """\
        How often to perform a health check for an instance. For example,
        specifying ``10s'' will run the check every 10 seconds. Valid units
        for this flag are ``s'' for seconds and ``m'' for minutes.
        The default value is ``5s''.
        """

    timeout_sec = parser.add_argument(
        '--timeout',
        help='How long to wait until check is a failure. Default is 5s.',
        type=arg_parsers.Duration(),
        default='5s')
    timeout_sec.detailed_help = """\
        If Google Compute Engine doesn't receive an HTTP 200 response from the
        instance by the time specified by the value of this flag, the health
        check request is considered a failure. For example, specifying ``10s''
        will cause the check to wait for 10 seconds before considering the
        request a failure.  Valid units for this flag are ``s'' for seconds and
        ``m'' for minutes.  The default value is ``5s''.
        """

    unhealthy_threshold = parser.add_argument(
        '--unhealthy-threshold',
        help='Consecutive failures to mark instance unhealthy. Default is 2.',
        type=int,
        default=2)
    unhealthy_threshold.detailed_help = """\
        The number of consecutive health check failures before a healthy
        instance is marked as unhealthy. The default is 2.
        """

    healthy_threshold = parser.add_argument(
        '--healthy-threshold',
        help='Consecutive successes to mark instance healthy. Default is 2.',
        type=int,
        default=2)
    healthy_threshold.detailed_help = """\
        The number of consecutive successful health checks before an
        unhealthy instance is marked as healthy. The default is 2.
        """

    parser.add_argument(
        '--description',
        help='An optional, textual description for the HTTP health check.')

  @property
  def service(self):
    return self.compute.httpHealthChecks

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'httpHealthChecks'

  def CreateRequests(self, args):
    """Returns the request necessary for adding the health check."""

    health_check_ref = self.HTTP_HEALTH_CHECKS_ARG.ResolveAsResource(
        args, self.resources)

    request = self.messages.ComputeHttpHealthChecksInsertRequest(
        httpHealthCheck=self.messages.HttpHealthCheck(
            name=health_check_ref.Name(),
            host=args.host,
            port=args.port,
            description=args.description,
            requestPath=args.request_path,
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold,
        ),
        project=self.project)

    return [request]


Create.detailed_help = {
    'brief': ('Create an HTTP health check to monitor load balanced instances'),
    'DESCRIPTION': """\
        *{command}* is used to create an HTTP health check. HTTP health checks
        monitor instances in a load balancer controlled by a target pool. All
        arguments to the command are optional except for the name of the health
        check. For more information on load balancing, see
        [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
        """,
}
