# Copyright 2016 Google Inc. All Rights Reserved.
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
"""High-level client for interacting with the Cloud Build API."""
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class BuildFailedError(exceptions.Error):
  """Raised when a Google Cloud Builder build fails."""


class CloudBuildClient(object):
  """High-level client for interacting with the Cloud Build API."""

  _RETRY_INTERVAL = 1
  _MAX_RETRIES = 60 * 60
  CLOUDBUILD_SUCCESS = 'SUCCESS'
  CLOUDBUILD_LOGFILE_FMT_STRING = 'log-{build_id}.txt'

  def __init__(self, client=None, messages=None):
    self.client = client or cloudbuild_util.GetClientInstance()
    self.messages = messages or cloudbuild_util.GetMessagesModule()

  # TODO(b/33173476): Convert `container builds submit` code to use this too
  def ExecuteCloudBuild(self, build, project=None):
    """Execute a call to CloudBuild service and wait for it to finish.


    Args:
      build: Build object. The Build to execute.
      project: The project to execute, or None to use the current project
          property.

    Raises:
      BuildFailedError: when the build fails.
    """
    if project is None:
      project = properties.VALUES.core.project.Get(required=True)

    build_op = self.client.projects_builds.Create(
        self.messages.CloudbuildProjectsBuildsCreateRequest(
            projectId=project,
            build=build,
        )
    )
    # Find build ID from operation metadata and print the logs URL.
    build_id = None
    logs_uri = None
    if build_op.metadata is not None:
      for prop in build_op.metadata.additionalProperties:
        if prop.key == 'build':
          for build_prop in prop.value.object_value.properties:
            if build_prop.key == 'id':
              build_id = build_prop.value.string_value
              if logs_uri is not None:
                break
            if build_prop.key == 'logUrl':
              logs_uri = build_prop.value.string_value
              if build_id is not None:
                break
          break

    if build_id is None:
      raise BuildFailedError('Could not determine build ID')

    self._WaitAndStreamLogs(build_op, build.logsBucket, build_id, logs_uri)

  def _WaitAndStreamLogs(self, build_op, logs_bucket, build_id, logs_uri):
    """Wait for a Cloud Build to finish, optionally streaming logs."""
    log.status.Print(
        'Started cloud build [{build_id}].'.format(build_id=build_id))
    if logs_bucket:
      log_object = self.CLOUDBUILD_LOGFILE_FMT_STRING.format(build_id=build_id)
      log_tailer = cloudbuild_logs.LogTailer(
          bucket=logs_bucket,
          obj=log_object)
      log_loc = None
      if logs_uri:
        log.status.Print('To see logs in the Cloud Console: ' + logs_uri)
        log_loc = 'at ' + logs_uri
      else:
        log.status.Print('Logs can be found in the Cloud Console.')
        log_loc = 'in the Cloud Console.'
      op = operations_util.WaitForOperation(
          operation_service=self.client.operations,
          operation=build_op,
          retry_interval=self._RETRY_INTERVAL,
          max_retries=self._MAX_RETRIES,
          retry_callback=log_tailer.Poll)
      # Poll the logs one final time to ensure we have everything. We know this
      # final poll will get the full log contents because GCS is strongly
      # consistent and Container Builder waits for logs to finish pushing before
      # marking the build complete.
      log_tailer.Poll(is_last=True)
    else:
      op = operations_util.WaitForOperation(
          operation_service=self.client.operations,
          operation=build_op,
          retry_interval=self._RETRY_INTERVAL,
          max_retries=self._MAX_RETRIES)

    final_status = _GetStatusFromOp(op)
    if final_status != self.CLOUDBUILD_SUCCESS:
      raise BuildFailedError('Cloud build failed with status '
                             + final_status + '. Check logs ' + log_loc)


def _GetStatusFromOp(op):
  """Get the Cloud Build Status from an Operation object.

  The op.response field is supposed to have a copy of the build object; however,
  the wire JSON from the server doesn't get deserialized into an actual build
  object. Instead, it is stored as a generic ResponseValue object, so we have
  to root around a bit.

  Args:
    op: the Operation object from a CloudBuild build request.

  Returns:
    string status, likely "SUCCESS" or "ERROR".
  """
  for prop in op.response.additionalProperties:
    if prop.key == 'status':
      return prop.value.string_value
  return 'UNKNOWN'
