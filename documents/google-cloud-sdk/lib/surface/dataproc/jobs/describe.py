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

"""Describe job command."""

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """View the details of a job.

  View the details of a job.

  ## EXAMPLES

  To view the details of a job, run:

    $ {command} job_id
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id',
        metavar='JOB_ID',
        help='The ID of the job to describe.')

  def Run(self, args):
    client = self.context['dataproc_client']

    job_ref = util.ParseJob(args.id, self.context)

    return client.projects_regions_jobs.Get(
        client.MESSAGES_MODULE.DataprocProjectsRegionsJobsGetRequest(
            projectId=job_ref.projectId,
            region=job_ref.region,
            jobId=job_ref.jobId))
