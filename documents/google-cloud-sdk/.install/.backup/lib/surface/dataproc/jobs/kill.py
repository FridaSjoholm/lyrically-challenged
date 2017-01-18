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

"""Kill job command."""

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Kill(base.Command):
  """Kill an active job.

  Kill an active job.

  ## EXAMPLES

  To cancel a job, run:

    $ {command} job_id
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id',
        metavar='JOB_ID',
        help='The ID of the job to kill.')

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    job_ref = util.ParseJob(args.id, self.context)
    request = messages.DataprocProjectsRegionsJobsCancelRequest(
        projectId=job_ref.projectId,
        region=job_ref.region,
        jobId=job_ref.jobId,
        cancelJobRequest=messages.CancelJobRequest())

    # TODO(user) Check if Job is still running and fail or handle 401.

    console_io.PromptContinue(
        message="The job '{0}' will be killed.".format(args.id),
        cancel_on_no=True,
        cancel_string='Cancellation aborted by user.')

    job = client.projects_regions_jobs.Cancel(request)
    log.status.Print(
        'Job cancellation initiated for [{0}].'.format(job_ref.jobId))

    job = util.WaitForJobTermination(
        job,
        self.context,
        message='Waiting for job cancellation',
        goal_state=messages.JobStatus.StateValueValuesEnum.CANCELLED)

    log.status.Print('Killed [{0}].'.format(job_ref))

    return job
