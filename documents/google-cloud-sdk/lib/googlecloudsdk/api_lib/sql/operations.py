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

"""Common utility functions for sql operations."""

import time

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.sql import errors
from googlecloudsdk.core.console import progress_tracker as console_progress_tracker
from googlecloudsdk.core.util import retry


class _BaseOperations(object):
  """Common utility functions for sql operations."""

  _PRE_START_SLEEP_SEC = 1
  _INITIAL_SLEEP_MS = 2000
  _MAX_WAIT_MS = 300000
  _WAIT_CEILING_MS = 20000
  _HTTP_MAX_RETRY_MS = 2000

  @classmethod
  def WaitForOperation(cls, sql_client, operation_ref, message):
    """Wait for a Cloud SQL operation to complete.

    No operation is done instantly. Wait for it to finish following this logic:
    First wait 1s, then query, then retry waiting exponentially more from 2s.
    We want to limit to 20s between retries to maintain some responsiveness.
    Finally, we want to limit the whole process to a conservative 300s. If we
    get to that point it means something is wrong and we can throw an exception.

    Args:
      sql_client: apitools.BaseApiClient, The client used to make requests.
      operation_ref: resources.Resource, A reference for the operation to poll.
      message: str, The string to print while polling.

    Returns:
      True if the operation succeeded without error.

    Raises:
      OperationError: If the operation has an error code, is in UNKNOWN state,
          or if the operation takes more than 300s.
    """

    def ShouldRetryFunc(result, state):
      # In case of HttpError, retry for up to _HTTP_MAX_RETRY_MS at most.
      if isinstance(result, exceptions.HttpError):
        if state.time_passed_ms > _BaseOperations._HTTP_MAX_RETRY_MS:
          raise result
        return True
      # In case of other Exceptions, raise them immediately.
      if isinstance(result, Exception):
        raise result
      # Otherwise let the retryer do it's job until the Operation is done.
      return not result

    with console_progress_tracker.ProgressTracker(
        message, autotick=False) as pt:
      time.sleep(_BaseOperations._PRE_START_SLEEP_SEC)
      retryer = retry.Retryer(exponential_sleep_multiplier=2,
                              max_wait_ms=_BaseOperations._MAX_WAIT_MS,
                              wait_ceiling_ms=_BaseOperations._WAIT_CEILING_MS)
      try:
        retryer.RetryOnResult(cls.GetOperationStatus,
                              [sql_client, operation_ref],
                              {'progress_tracker': pt},
                              should_retry_if=ShouldRetryFunc,
                              sleep_ms=_BaseOperations._INITIAL_SLEEP_MS)
      except retry.WaitException:
        raise errors.OperationError(
            ('Operation {0} is taking longer than expected. You can continue '
             'waiting for the operation by running `{1}`').format(
                 operation_ref,
                 cls.GetOperationWaitCommand(operation_ref)))


class OperationsV1Beta3(_BaseOperations):
  """Common utility functions for sql operations V1Beta3."""

  @staticmethod
  def GetOperationStatus(sql_client, operation_ref, progress_tracker=None):
    """Helper function for getting the status of an operation for V1Beta3 API.

    Args:
      sql_client: apitools.BaseApiClient, The client used to make requests.
      operation_ref: resources.Resource, A reference for the operation to poll.
      progress_tracker: progress_tracker.ProgressTracker, A reference for the
          progress tracker to tick, in case this function is used in a Retryer.

    Returns:
      True: if the operation succeeded without error.
      False: if the operation is not yet done.
      OperationError: If the operation has an error code or is in UNKNOWN state.
      Exception: Any other exception that can occur when calling Get
    """

    if progress_tracker:
      progress_tracker.Tick()
    try:
      op = sql_client.operations.Get(
          sql_client.MESSAGES_MODULE.SqlOperationsGetRequest(
              project=operation_ref.project,
              instance=operation_ref.instance,
              operation=operation_ref.operation))
    except Exception as e:  # pylint:disable=broad-except
      # Since we use this function in a retryer.RetryOnResult block, where we
      # retry for different exceptions up to different amounts of time, we
      # have to catch all exceptions here and return them.
      return e
    if op.error:
      return errors.OperationError(op.error[0].code)
    if op.state == 'UNKNOWN':
      return errors.OperationError(op.state)
    if op.state == 'DONE':
      return True
    return False

  @staticmethod
  def GetOperationWaitCommand(operation_ref):
    return 'gcloud sql operations wait -i {0} --project {1} {2}'.format(
        operation_ref.instance, operation_ref.project, operation_ref.operation)


class OperationsV1Beta4(_BaseOperations):
  """Common utility functions for sql operations V1Beta4."""

  @staticmethod
  def GetOperationStatus(sql_client, operation_ref, progress_tracker=None):
    """Helper function for getting the status of an operation for V1Beta4 API.

    Args:
      sql_client: apitools.BaseApiClient, The client used to make requests.
      operation_ref: resources.Resource, A reference for the operation to poll.
      progress_tracker: progress_tracker.ProgressTracker, A reference for the
          progress tracker to tick, in case this function is used in a Retryer.

    Returns:
      True: if the operation succeeded without error.
      False: if the operation is not yet done.
      OperationError: If the operation has an error code or is in UNKNOWN state.
      Exception: Any other exception that can occur when calling Get
    """

    if progress_tracker:
      progress_tracker.Tick()
    try:
      op = sql_client.operations.Get(
          sql_client.MESSAGES_MODULE.SqlOperationsGetRequest(
              project=operation_ref.project,
              operation=operation_ref.operation))
    except Exception as e:  # pylint:disable=broad-except
      # Since we use this function in a retryer.RetryOnResult block, where we
      # retry for different exceptions up to different amounts of time, we
      # have to catch all exceptions here and return them.
      return e
    if op.error and op.error.errors:
      return errors.OperationError(op.error.errors[0].code)
    if op.status == 'UNKNOWN':
      return errors.OperationError(op.status)
    if op.status == 'DONE':
      return True
    return False

  @staticmethod
  def GetOperationWaitCommand(operation_ref):
    return 'gcloud beta sql operations wait --project {0} {1}'.format(
        operation_ref.project, operation_ref.operation)
