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

"""Common utilities for the gcloud dataproc tool."""

import time
import urlparse
import uuid

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


def FormatRpcError(error):
  """Returns a printable representation of a failed Google API's status.proto.

  Args:
    error: the failed Status to print.

  Returns:
    A ready-to-print string representation of the error.
  """
  log.debug('Error:\n' + encoding.MessageToJson(error))
  formatted_error = error.message
  # Only display details if the log level is INFO or finer.
  if error.details and log.GetVerbosity() <= log.info:
    formatted_error += (
        '\nDetails:\n' + encoding.MessageToJson(error.details))
  return formatted_error


# TODO(user): Create a common wait_utils class to reuse common code.
def WaitForOperation(
    operation, context, message, timeout_s=2100, poll_period_s=5):
  """Poll dataproc Operation until its status is done or timeout reached.

  Args:
    operation: Operation, message of the operation to be polled.
    context: dict, dataproc Command context.
    message: str, message to display to user while polling.
    timeout_s: number, seconds to poll with retries before timing out.
    poll_period_s: number, delay in seconds between requests.

  Returns:
    Operation: the return value of the last successful operations.get
    request.

  Raises:
    OperationError: if the operation times out or finishes with an error.
  """
  client = context['dataproc_client']
  messages = context['dataproc_messages']

  request = messages.DataprocProjectsRegionsOperationsGetRequest(
      name=operation.name)
  log.status.Print('Waiting on operation [{0}].'.format(operation.name))
  start_time = time.time()
  with progress_tracker.ProgressTracker(message, autotick=True):
    while timeout_s > (time.time() - start_time):
      try:
        operation = client.projects_regions_operations.Get(request)
        if operation.done:
          break
      except apitools_exceptions.HttpError:
        # Keep trying until we timeout in case error is transient.
        pass
      time.sleep(poll_period_s)
  # TODO(user): Parse operation metadata.
  log.debug('Operation:\n' + encoding.MessageToJson(operation))
  if not operation.done:
    raise exceptions.OperationTimeoutError(
        'Operation [{0}] timed out.'.format(operation.name))
  elif operation.error:
    raise exceptions.OperationError(
        'Operation [{0}] failed: {1}.'.format(
            operation.name, FormatRpcError(operation.error)))

  log.info('Operation [%s] finished after %.3f seconds',
           operation.name, (time.time() - start_time))
  return operation


def WaitForResourceDeletion(
    request_method,
    resource_ref,
    message,
    timeout_s=60,
    poll_period_s=5):
  """Poll Dataproc resource until it no longer exists."""
  with progress_tracker.ProgressTracker(message, autotick=True):
    start_time = time.time()
    while timeout_s > (time.time() - start_time):
      try:
        request_method(resource_ref)
      except apitools_exceptions.HttpError as error:
        if error.status_code == 404:
          # Object deleted
          return
        log.debug('Get request for [{0}] failed:\n{1}', resource_ref, error)
        # Keep trying until we timeout in case error is transient.
      time.sleep(poll_period_s)
  raise exceptions.OperationTimeoutError(
      'Deleting resource [{0}] timed out.'.format(resource_ref))


class NoOpProgressDisplay(object):
  """For use in place of a ProgressTracker in a 'with' block."""

  def __enter__(self):
    pass

  def __exit__(self, *unused_args):
    pass


def WaitForJobTermination(
    job,
    context,
    message,
    goal_state,
    stream_driver_log=False,
    log_poll_period_s=1,
    dataproc_poll_period_s=10,
    timeout_s=None):
  """Poll dataproc Job until its status is terminal or timeout reached.

  Args:
    job: The job to wait to finish.
    context: dict, dataproc Command context.
    message: str, message to display to user while polling.
    goal_state: JobStatus.StateValueValuesEnum, the state to define success
    stream_driver_log: bool, Whether to show the Job's driver's output.
    log_poll_period_s: number, delay in seconds between checking on the log.
    dataproc_poll_period_s: number, delay in seconds between requests to
        the Dataproc API.
    timeout_s: number, time out for job completion. None means no timeout.

  Returns:
    Operation: the return value of the last successful operations.get
    request.

  Raises:
    OperationError: if the operation times out or finishes with an error.
  """
  client = context['dataproc_client']
  job_ref = ParseJob(job.reference.jobId, context)
  request = client.MESSAGES_MODULE.DataprocProjectsRegionsJobsGetRequest(
      projectId=job_ref.projectId,
      region=job_ref.region,
      jobId=job_ref.jobId)
  driver_log_stream = None
  last_job_poll_time = 0
  job_complete = False
  wait_display = None

  def ReadDriverLogIfPresent():
    if driver_log_stream and driver_log_stream.open:
      # TODO(user): Don't read all output.
      driver_log_stream.ReadIntoWritable(log.err)

  if stream_driver_log:
    log.status.Print('Waiting for job output...')
    wait_display = NoOpProgressDisplay()
  else:
    wait_display = progress_tracker.ProgressTracker(message, autotick=True)
  start_time = now = time.time()
  with wait_display:
    while not timeout_s or timeout_s > (now - start_time):
      # Poll logs first to see if it closed.
      ReadDriverLogIfPresent()
      log_stream_closed = driver_log_stream and not driver_log_stream.open
      if not job_complete and job.status.state in constants.TERMINAL_JOB_STATES:
        job_complete = True
        # Wait an 10s to get trailing output.
        timeout_s = now - start_time + 10

      if job_complete and (not stream_driver_log or log_stream_closed):
        # Nothing left to wait for
        break

      regular_job_poll = (
          not job_complete
          # Poll less frequently on dataproc API
          and now >= last_job_poll_time + dataproc_poll_period_s)
      # Poll at regular frequency before output has streamed and after it has
      # finished.
      expecting_output_stream = stream_driver_log and not driver_log_stream
      expecting_job_done = not job_complete and log_stream_closed
      if regular_job_poll or expecting_output_stream or expecting_job_done:
        last_job_poll_time = now
        try:
          job = client.projects_regions_jobs.Get(request)
          if (stream_driver_log
              and not driver_log_stream
              and job.driverOutputResourceUri):
            driver_log_stream = storage_helpers.StorageObjectSeriesStream(
                job.driverOutputResourceUri)
        except apitools_exceptions.HttpError as error:
          log.warn('GetJob failed:\n%s', error)
          # Keep trying until we timeout in case error is transient.
      time.sleep(log_poll_period_s)
      now = time.time()

  state = job.status.state
  if state is not goal_state and job.status.details:
    # Just log details, because the state will be in the error message.
    log.info(job.status.details)

  if state in constants.TERMINAL_JOB_STATES:
    if stream_driver_log:
      if not driver_log_stream:
        log.warn('Expected job output not found.')
      elif driver_log_stream.open:
        log.warn('Job terminated, but output did not finish streaming.')
    if state is goal_state:
      return job
    raise exceptions.JobError(
        'Job [{0}] entered state [{1}] while waiting for [{2}].'.format(
            job_ref.jobId, state, goal_state))
  raise exceptions.JobTimeoutError(
      'Job [{0}] timed out while in state [{1}].'.format(
          job_ref.jobId, state))


def ParseCluster(name, context):
  resources = context['resources']
  ref = resources.Parse(name, collection='dataproc.projects.regions.clusters')
  return ref


def ParseJob(job_id, context):
  resources = context['resources']
  ref = resources.Parse(job_id, collection='dataproc.projects.regions.jobs')
  return ref


def ParseOperation(operation, context):
  resources = context['resources']
  collection = 'dataproc.projects.regions.operations'
  # Dataproc usually refers to Operations by relative name, which must be
  # parsed explicitly until resources.Parse supports it.
  # TODO(user): Remove once Parse delegates to ParseRelativeName.
  url = urlparse.urlparse(operation)
  if not url.scheme and '/' in url.path and not url.path.startswith('/'):
    return resources.ParseRelativeName(operation, collection=collection)
  return resources.Parse(operation, collection=collection)


def GetJobId(job_id=None):
  if job_id:
    return job_id
  return str(uuid.uuid4())


class Bunch(object):
  """Class that converts a dictionary to javascript like object.

  For example:
      Bunch({'a': {'b': {'c': 0}}}).a.b.c == 0
  """

  def __init__(self, dictionary):
    for key, value in dictionary.iteritems():
      if isinstance(value, dict):
        value = Bunch(value)
      self.__dict__[key] = value


def AddJvmDriverFlags(parser):
  parser.add_argument(
      '--jar',
      dest='main_jar',
      help='The HCFS URI of jar file containing the driver jar.')
  parser.add_argument(
      '--class',
      dest='main_class',
      help=('The class containing the main method of the driver. Must be in a'
            ' provided jar or jar that is already on the classpath'))
