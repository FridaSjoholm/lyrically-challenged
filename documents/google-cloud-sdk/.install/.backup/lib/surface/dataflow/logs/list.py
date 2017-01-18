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
"""Implementation of gcloud dataflow logs list command.
"""

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.command_lib.dataflow import time_util
from googlecloudsdk.core.resource import resource_projection_spec


class List(base.ListCommand):
  """Retrieve the job logs for a specific job.

  Retrieves the job logs from a specified job using the Dataflow Messages API
  with at least the specified importance level. Can also be used to display
  logs between a given time period using the --before and --after flags. These
  logs are produced by the service and are distinct from worker logs. Worker
  logs can be found in Cloud Logging.

  ## EXAMPLES

  Retrieve only error logs:

    $ {command} --importance=error

  Retrieve all logs after some date:

    $ {command} --after="2016-08-12 00:00:00"
  """

  @staticmethod
  def Args(parser):
    job_utils.ArgsForJobRef(parser)

    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    base.ASYNC_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)

    parser.add_argument(
        '--after',
        type=time_util.ParseTimeArg,
        help='Only display messages logged after the given time. Time format is'
        ' yyyy-mm-dd hh-mm-ss')
    parser.add_argument(
        '--before',
        type=time_util.ParseTimeArg,
        help='Only display messages logged before the given time. Time format'
        ' is yyyy-mm-dd hh-mm-ss')
    parser.add_argument(
        '--importance',
        choices=['debug', 'detailed', 'warning', 'error'],
        default='warning',
        help='Minimum importance a message must have to be displayed.')

  def Collection(self):
    return 'dataflow.logs'

  def Defaults(self):
    importances = {
        'JOB_MESSAGE_DETAILED': 'd',
        'JOB_MESSAGE_DEBUG': 'D',
        'JOB_MESSAGE_WARNING': 'W',
        'JOB_MESSAGE_ERROR': 'E',
    }
    symbols = {'dataflow.JobMessage::enum': importances}
    return resource_projection_spec.ProjectionSpec(symbols=symbols)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      None on success, or a string containing the error message.
    """
    job_ref = job_utils.ExtractJobRef(args.job)

    importance_enum = (
        apis.Messages.LIST_REQUEST.MinimumImportanceValueValuesEnum)
    importance_map = {
        'debug': importance_enum.JOB_MESSAGE_DEBUG,
        'detailed': importance_enum.JOB_MESSAGE_DETAILED,
        'error': importance_enum.JOB_MESSAGE_ERROR,
        'warning': importance_enum.JOB_MESSAGE_WARNING,
    }

    request = apis.Messages.LIST_REQUEST(
        projectId=job_ref.projectId,
        jobId=job_ref.jobId,
        minimumImportance=(args.importance and importance_map[args.importance]),

        # Note: It if both are present, startTime > endTime, because we will
        # return messages with actual time [endTime, startTime).
        startTime=args.after and time_util.Strftime(args.after),
        endTime=args.before and time_util.Strftime(args.before))

    return dataflow_util.YieldFromList(
        job_id=job_ref.jobId,
        project_id=job_ref.projectId,
        service=apis.Messages.GetService(),
        request=request,
        batch_size=args.limit,
        batch_size_attribute='pageSize',
        field='jobMessages')
