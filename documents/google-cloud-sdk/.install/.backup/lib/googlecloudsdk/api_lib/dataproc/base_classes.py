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

"""Base command classes for shared logic between gcloud dataproc commands."""

import abc
import os
import urlparse

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class JobSubmitter(base.Command):
  """Submit a job to a cluster."""

  __metaclass__ = abc.ABCMeta

  def __init__(self, *args, **kwargs):
    super(JobSubmitter, self).__init__(*args, **kwargs)
    self.files_by_type = {}
    self.files_to_stage = []
    self._staging_dir = None

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--cluster',
        required=True,
        help='The Dataproc cluster to submit the job to.')

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    job_id = util.GetJobId(args.id)
    job_ref = util.ParseJob(job_id, self.context)

    self.PopulateFilesByType(args)

    cluster_ref = util.ParseCluster(args.cluster, self.context)
    request = messages.DataprocProjectsRegionsClustersGetRequest(
        projectId=cluster_ref.projectId,
        region=cluster_ref.region,
        clusterName=cluster_ref.clusterName)

    cluster = client.projects_regions_clusters.Get(request)

    self._staging_dir = self.GetStagingDir(cluster, job_ref.jobId)
    self.ValidateAndStageFiles()

    job = messages.Job(
        reference=messages.JobReference(
            projectId=job_ref.projectId,
            jobId=job_ref.jobId),
        placement=messages.JobPlacement(
            clusterName=args.cluster))

    self.ConfigureJob(job, args)

    request = messages.DataprocProjectsRegionsJobsSubmitRequest(
        projectId=job_ref.projectId,
        region=job_ref.region,
        submitJobRequest=messages.SubmitJobRequest(
            job=job))

    job = client.projects_regions_jobs.Submit(request)

    log.status.Print('Job [{0}] submitted.'.format(job_id))

    if not args.async:
      job = util.WaitForJobTermination(
          job,
          self.context,
          message='Waiting for job completion',
          goal_state=messages.JobStatus.StateValueValuesEnum.DONE,
          stream_driver_log=True)
      log.status.Print('Job [{0}] finished successfully.'.format(job_id))

    return job

  def _GetStagedFile(self, file_str):
    """Validate file URI and register it for uploading if it is local."""
    drive, _ = os.path.splitdrive(file_str)
    uri = urlparse.urlsplit(file_str, allow_fragments=False)
    # Determine the file is local to this machine if no scheme besides a drive
    # is passed. file:// URIs are interpreted as living on VMs.
    is_local = drive or not uri.scheme
    if not is_local:
      # Non-local files are already staged.
      # TODO(user): Validate scheme.
      return file_str

    if not os.path.exists(file_str):
      raise files.Error('File Not Found: [{0}].'.format(file_str))
    basename = os.path.basename(file_str)
    self.files_to_stage.append(file_str)
    staged_file = urlparse.urljoin(self._staging_dir, basename)
    return staged_file

  def ValidateAndStageFiles(self):
    """Validate file URIs and upload them if they are local."""
    for file_type, file_or_files in self.files_by_type.iteritems():
      # TODO(user): Validate file suffixes.
      if not file_or_files:
        continue
      elif isinstance(file_or_files, str):
        self.files_by_type[file_type] = self._GetStagedFile(file_or_files)
      else:
        staged_files = [self._GetStagedFile(f) for f in file_or_files]
        self.files_by_type[file_type] = staged_files

    if self.files_to_stage:
      log.info(
          'Staging local files {0} to {1}.'.format(
              self.files_to_stage, self._staging_dir))
      storage_helpers.Upload(self.files_to_stage, self._staging_dir)

  def GetStagingDir(self, cluster, job_id):
    """Determine the GCS directory to stage job resources in."""
    staging_dir = (
        'gs://{bucket}/{prefix}/{uuid}/jobs/{job_id}/staging/'.format(
            bucket=cluster.config.configBucket,
            prefix=constants.GCS_METADATA_PREFIX,
            uuid=cluster.clusterUuid,
            job_id=job_id))
    return staging_dir

  def BuildLoggingConfig(self, driver_logging):
    """Build LoggingConfig from parameters."""
    if not driver_logging:
      return None

    messages = self.context['dataproc_messages']

    return messages.LoggingConfig(
        driverLogLevels=encoding.DictToMessage(
            driver_logging,
            messages.LoggingConfig.DriverLogLevelsValue))

  @abc.abstractmethod
  def ConfigureJob(self, job, args):
    """Add type-specific job configuration to job message."""
    pass

  @abc.abstractmethod
  def PopulateFilesByType(self, args):
    """Take files out of args to allow for them to be staged."""
    pass


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class JobSubmitterBeta(JobSubmitter):
  """Submit a job to a cluster."""

  @staticmethod
  def Args(parser):
    JobSubmitter.Args(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def ConfigureJob(self, job, args):
    messages = self.context['dataproc_messages']

    # Parse labels (if present)
    labels = labels_util.UpdateLabels(
        None,
        messages.Job.LabelsValue,
        labels_util.GetUpdateLabelsDictFromArgs(args),
        None)
    job.labels = labels
