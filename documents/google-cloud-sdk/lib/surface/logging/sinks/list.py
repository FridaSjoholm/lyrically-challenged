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

"""'logging sinks list' command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """Lists the defined sinks."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--only-project-sinks', required=False, action='store_true',
        help='Display only project sinks.')

  def Collection(self):
    return 'logging.sinks'

  def ListLogSinks(self, project, log_name):
    """List log sinks from the specified log."""
    result = util.GetClientV1().projects_logs_sinks.List(
        util.GetMessagesV1().LoggingProjectsLogsSinksListRequest(
            projectsId=project, logsId=log_name))
    for sink in result.sinks:
      yield util.TypedLogSink(sink, log_name=log_name)

  def ListLogServiceSinks(self, project, service_name):
    """List log service sinks from the specified service."""
    result = util.GetClientV1().projects_logServices_sinks.List(
        util.GetMessagesV1().LoggingProjectsLogServicesSinksListRequest(
            projectsId=project, logServicesId=service_name))
    for sink in result.sinks:
      yield util.TypedLogSink(sink, service_name=service_name)

  def ListProjectSinks(self, project):
    """List project sinks from the specified project."""
    # Use V2 logging API for project sinks.
    result = util.GetClient().projects_sinks.List(
        util.GetMessages().LoggingProjectsSinksListRequest(
            parent='projects/{0}'.format(project)))
    for sink in result.sinks:
      yield util.TypedLogSink(sink)

  def YieldAllSinks(self, project):
    """Yield all log and log service sinks from the specified project."""
    client = util.GetClientV1()
    messages = util.GetMessagesV1()
    # First get all the log sinks.
    response = list_pager.YieldFromList(
        client.projects_logs,
        messages.LoggingProjectsLogsListRequest(projectsId=project),
        field='logs', batch_size=None, batch_size_attribute='pageSize')
    for log in response:
      # We need only the base log name, not the full resource uri.
      log_id = util.ExtractLogId(log.name)
      for typed_sink in self.ListLogSinks(project, log_id):
        yield typed_sink
    # Now get all the log service sinks.
    response = list_pager.YieldFromList(
        client.projects_logServices,
        messages.LoggingProjectsLogServicesListRequest(projectsId=project),
        field='logServices', batch_size=None, batch_size_attribute='pageSize')
    for service in response:
      # In contrast, service.name correctly contains only the name.
      for typed_sink in self.ListLogServiceSinks(project, service.name):
        yield typed_sink
    # Lastly, get all project sinks.
    for typed_sink in self.ListProjectSinks(project):
      yield typed_sink

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of sinks.
    """
    project = properties.VALUES.core.project.Get(required=True)

    if args.log:
      return self.ListLogSinks(project, args.log)
    elif args.service:
      return self.ListLogServiceSinks(project, args.service)
    elif args.only_project_sinks:
      return self.ListProjectSinks(project)
    else:
      return self.YieldAllSinks(project)

List.detailed_help = {
    'DESCRIPTION': """\
        {index}
        If either the *--log* or *--log-service* flags are included, then
        the only sinks listed are for that log or that service.
        If *--only-project-sinks* flag is included, then only project sinks
        are listed.
        If none of the flags are included, then all sinks in use are listed.
    """,
}
