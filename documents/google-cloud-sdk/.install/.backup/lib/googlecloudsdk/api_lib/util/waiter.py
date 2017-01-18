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

"""Utilities to support long running operations."""

import abc
import sys
import time

from apitools.base.py import encoding
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry


_TIMEOUT_MESSAGE = (
    'The operations may still be underway remotely and may still succeed; '
    'use gcloud list and describe commands or '
    'https://console.developers.google.com/ to check resource state.')


class TimeoutError(exceptions.Error):
  pass


class AbortWaitError(exceptions.Error):
  pass


class OperationError(exceptions.Error):
  pass


class OperationPoller(object):
  """Interface for defining operation which can be polled and waited on.

  This construct manages operation_ref, operation and result abstract objects.
  Operation_ref is an identifier for operation which is a proxy for result
  object. OperationPoller has three responsibilities:
    1. Given operation object determine if it is done.
    2. Given operation_ref fetch operation object
    3. Given operation object fetch result object
  """
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def IsDone(self, operation):
    """Given result of Poll determines if result is done.

    Args:
      operation: object representing operation returned by Poll method.

    Returns:

    """
    return True

  @abc.abstractmethod
  def Poll(self, operation_ref):
    """Retrieves operation given its reference.

    Args:
      operation_ref: str, some id for operation.

    Returns:
      object which represents operation.
    """
    return None

  @abc.abstractmethod
  def GetResult(self, operation):
    """Given operation message retrieves result it represents.

    Args:
      operation: object, representing operation returned by Poll method.
    Returns:
      some object created by given operation.
    """
    return None


class CloudOperationPoller(OperationPoller):
  """Manages a longrunning Operations.

  See https://cloud.google.com/speech/reference/rpc/google.longrunning
  """

  def __init__(self, result_service, operation_service):
    """Sets up poller for cloud operations.

    Args:
      result_service: apitools.base.py.base_api.BaseApiService, api service for
        retrieving created result of initiated operation.
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.

      Note that result_service and operation_service Get request must have
      single attribute called 'name'.
    """
    self.result_service = result_service
    self.operation_service = operation_service

  def IsDone(self, operation):
    """Overrides."""
    if operation.done:
      if operation.error:
        raise OperationError(operation.error.message)
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_service.GetRequestType('Get')
    return self.operation_service.Get(
        request_type(name=operation_ref.RelativeName()))

  def GetResult(self, operation):
    """Overrides.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      result of result_service.Get request.
    """
    request_type = self.result_service.GetRequestType('Get')
    response_dict = encoding.MessageToPyValue(operation.response)
    return self.result_service.Get(request_type(name=response_dict['name']))


def WaitFor(poller, operation_ref, message,
            pre_start_sleep_ms=1000,
            max_retrials=None,
            max_wait_ms=1800000,
            exponential_sleep_multiplier=1.4,
            jitter_ms=1000,
            wait_ceiling_ms=180000,
            sleep_ms=2000):
  """Waits with retrues for operation to be done given poller.

  Args:
    poller: OperationPoller, poller to use during retrials.
    operation_ref: object, passed to operation poller poll method.
    message: str, string to display for progrss_tracker.
    pre_start_sleep_ms: int, Time to wait before making first poll request.
    max_retrials: int, max number of retrials before raising RetryException.
    max_wait_ms: int, number of ms to wait before raising WaitException.
    exponential_sleep_multiplier: float, factor to use on subsequent retries.
    jitter_ms: int, random (up to the value) additional sleep between retries.
    wait_ceiling_ms: int, Maximum wait between retries.
    sleep_ms: int or iterable: for how long to wait between trials.

  Returns:
    poller.GetResult(operation).

  Raises:
    AbortWaitError: if ctrl-c was pressed.
    TimeoutError: if retryer has finished wihout being done.
  """

  def _CtrlCHandler(unused_signal, unused_frame):
    raise AbortWaitError('Ctrl-C aborted wait.')

  try:
    with execution_utils.CtrlCSection(_CtrlCHandler):
      try:
        with progress_tracker.ProgressTracker(message) as tracker:

          if pre_start_sleep_ms:
            _SleepMs(pre_start_sleep_ms)

          def _StatusUpdate(unused_result, unused_status):
            tracker.Tick()

          retryer = retry.Retryer(
              max_retrials=max_retrials,
              max_wait_ms=max_wait_ms,
              exponential_sleep_multiplier=exponential_sleep_multiplier,
              jitter_ms=jitter_ms,
              wait_ceiling_ms=wait_ceiling_ms,
              status_update_func=_StatusUpdate)

          def _IsNotDone(operation, unused_state):
            return not poller.IsDone(operation)

          operation = retryer.RetryOnResult(
              func=poller.Poll,
              args=(operation_ref,),
              should_retry_if=_IsNotDone,
              sleep_ms=sleep_ms)
      except retry.WaitException:
        raise TimeoutError(
            'Operation {0} has not finished in {1} seconds. {2}'
            .format(operation_ref, int(max_wait_ms / 1000), _TIMEOUT_MESSAGE))
      except retry.MaxRetrialsException as e:
        raise TimeoutError(
            'Operation {0} has not finished in {1} seconds '
            'after max {2} retrials. {3}'
            .format(operation_ref,
                    int(e.state.time_passed_ms / 1000),
                    e.state.retrial,
                    _TIMEOUT_MESSAGE))

  except AbortWaitError:
    # Write this out now that progress tracker is done.
    sys.stderr.write('Aborting wait for operation {0}.\n'.format(operation_ref))
    raise

  return poller.GetResult(operation)


def _SleepMs(miliseconds):
  time.sleep(miliseconds / 1000)

