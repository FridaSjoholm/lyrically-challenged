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

"""'logging metrics list' command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """Displays all logs-based metrics."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Collection(self):
    return 'logging.metrics'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of metrics.
    """
    request = util.GetMessages().LoggingProjectsMetricsListRequest(
        parent=util.GetCurrentProjectParent())

    return list_pager.YieldFromList(
        util.GetClient().projects_metrics, request, field='metrics',
        limit=args.limit, batch_size=None, batch_size_attribute='pageSize')


List.detailed_help = {
    'DESCRIPTION': """\
        Lists all logs-based metrics.
    """,
    'EXAMPLES': """\
          $ {command} --limit=10
    """,
}
