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
"""Command for updating HTTPS health checks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.https_health_checks import flags

THRESHOLD_UPPER_BOUND = 10
THRESHOLD_LOWER_BOUND = 1
TIMEOUT_UPPER_BOUND_SEC = 300
TIMEOUT_LOWER_BOUND_SEC = 1
CHECK_INTERVAL_UPPER_BOUND_SEC = 300
CHECK_INTERVAL_LOWER_BOUND_SEC = 1


class Update(base_classes.ReadWriteCommand):
  """Update an HTTPS health check."""

  HTTPS_HEALTH_CHECKS_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HTTPS_HEALTH_CHECKS_ARG = flags.HttpsHealthCheckArgument()
    cls.HTTPS_HEALTH_CHECKS_ARG.AddArgument(parser)

    host = parser.add_argument(
        '--host',
        help='The value of the host header used by the HTTPS health check.')
    host.detailed_help = """\
        The value of the host header used in this HTTPS health check request.
        By default, this is empty and Google Compute Engine automatically sets
        the host header in health requests to the same external IP address as
        the forwarding rule associated with the target pool. Setting this to
        an empty string will clear any existing host value.
        """

    port = parser.add_argument(
        '--port',
        help='The TCP port number for the health request.',
        type=int)
    port.detailed_help = """\
        The TCP port number that this health check monitors.
        """

    request_path = parser.add_argument(
        '--request-path',
        help='The request path for the health check.')
    request_path.detailed_help = """\
        The request path that this health check monitors. For example,
        ``/healthcheck''.
        """

    check_interval_sec = parser.add_argument(
        '--check-interval',
        help='How often to run the check.',
        type=arg_parsers.Duration())
    check_interval_sec.detailed_help = """\
        How often to perform a health check for an instance. For example,
        specifying ``10s'' will run the check every 10 seconds. Valid units
        for this flag are ``s'' for seconds and ``m'' for minutes.
        """

    timeout_sec = parser.add_argument(
        '--timeout',
        help='How long to wait until check is a failure.',
        type=arg_parsers.Duration())
    timeout_sec.detailed_help = """\
        If Google Compute Engine doesn't receive an HTTPS 200 response from the
        instance by the time specified by the value of this flag, the health
        check request is considered a failure. For example, specifying ``10s''
        will cause the check to wait for 10 seconds before considering the
        request a failure.  Valid units for this flag are ``s'' for seconds and
        ``m'' for minutes.
        """

    unhealthy_threshold = parser.add_argument(
        '--unhealthy-threshold',
        help='Consecutive failures to mark instance unhealthy.',
        type=int)
    unhealthy_threshold.detailed_help = """\
        The number of consecutive health check failures before a healthy
        instance is marked as unhealthy.
        """

    healthy_threshold = parser.add_argument(
        '--healthy-threshold',
        help='Consecutive successes to mark instance healthy.',
        type=int)
    healthy_threshold.detailed_help = """\
        The number of consecutive successful health checks before an
        unhealthy instance is marked as healthy.
        """

    parser.add_argument(
        '--description',
        help=('A textual description for the HTTPS health check. Pass in an '
              'empty string to unset.'))

  @property
  def service(self):
    return self.compute.httpsHealthChecks

  @property
  def resource_type(self):
    return 'httpsHealthChecks'

  def CreateReference(self, args):
    return self.HTTPS_HEALTH_CHECKS_ARG.ResolveAsResource(
        args, self.resources)

  def GetGetRequest(self, args):
    """Returns a request for fetching the existing HTTPS health check."""
    return (self.service,
            'Get',
            self.messages.ComputeHttpsHealthChecksGetRequest(
                httpsHealthCheck=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    """Returns a request for updated the HTTPS health check."""
    return (self.service,
            'Update',
            self.messages.ComputeHttpsHealthChecksUpdateRequest(
                httpsHealthCheck=self.ref.Name(),
                httpsHealthCheckResource=replacement,
                project=self.project))

  def Modify(self, args, existing_check):
    """Returns a modified HttpsHealthCheck message."""
    # Description and Host are the only attributes that can be cleared by
    # passing in an empty string (but we don't want to set it to an empty
    # string).
    if args.description:
      description = args.description
    elif args.description is None:
      description = existing_check.description
    else:
      description = None

    if args.host:
      host = args.host
    elif args.host is None:
      host = existing_check.host
    else:
      host = None

    new_health_check = self.messages.HttpsHealthCheck(
        name=existing_check.name,
        host=host,
        port=args.port or existing_check.port,
        description=description,
        requestPath=args.request_path or existing_check.requestPath,
        checkIntervalSec=(args.check_interval or
                          existing_check.checkIntervalSec),
        timeoutSec=args.timeout or existing_check.timeoutSec,
        healthyThreshold=(args.healthy_threshold or
                          existing_check.healthyThreshold),
        unhealthyThreshold=(args.unhealthy_threshold or
                            existing_check.unhealthyThreshold),
    )
    return new_health_check

  def Run(self, args):
    if (args.check_interval is not None
        and (args.check_interval < CHECK_INTERVAL_LOWER_BOUND_SEC
             or args.check_interval > CHECK_INTERVAL_UPPER_BOUND_SEC)):
      raise exceptions.ToolException(
          '[--check-interval] must not be less than {0} second or greater '
          'than {1} seconds; received [{2}] seconds.'.format(
              CHECK_INTERVAL_LOWER_BOUND_SEC, CHECK_INTERVAL_UPPER_BOUND_SEC,
              args.check_interval))

    if (args.timeout is not None
        and (args.timeout < TIMEOUT_LOWER_BOUND_SEC
             or args.timeout > TIMEOUT_UPPER_BOUND_SEC)):
      raise exceptions.ToolException(
          '[--timeout] must not be less than {0} second or greater than {1} '
          'seconds; received: [{2}] seconds.'.format(
              TIMEOUT_LOWER_BOUND_SEC, TIMEOUT_UPPER_BOUND_SEC, args.timeout))

    if (args.healthy_threshold is not None
        and (args.healthy_threshold < THRESHOLD_LOWER_BOUND
             or args.healthy_threshold > THRESHOLD_UPPER_BOUND)):
      raise exceptions.ToolException(
          '[--healthy-threshold] must be an integer between {0} and {1}, '
          'inclusive; received: [{2}].'.format(THRESHOLD_LOWER_BOUND,
                                               THRESHOLD_UPPER_BOUND,
                                               args.healthy_threshold))

    if (args.unhealthy_threshold is not None
        and (args.unhealthy_threshold < THRESHOLD_LOWER_BOUND
             or args.unhealthy_threshold > THRESHOLD_UPPER_BOUND)):
      raise exceptions.ToolException(
          '[--unhealthy-threshold] must be an integer between {0} and {1}, '
          'inclusive; received [{2}].'.format(THRESHOLD_LOWER_BOUND,
                                              THRESHOLD_UPPER_BOUND,
                                              args.unhealthy_threshold))

    args_unset = not (args.port
                      or args.request_path
                      or args.check_interval
                      or args.timeout
                      or args.healthy_threshold
                      or args.unhealthy_threshold)
    if args.description is None and args.host is None and args_unset:
      raise exceptions.ToolException('At least one property must be modified.')

    return super(Update, self).Run(args)


Update.detailed_help = {
    'brief': ('Update an HTTPS health check'),
    'DESCRIPTION': """\
        *{command}* is used to update an existing HTTPS health check. Only
        arguments passed in will be updated on the health check. Other
        attributes will remain unaffected.
        """,
}
