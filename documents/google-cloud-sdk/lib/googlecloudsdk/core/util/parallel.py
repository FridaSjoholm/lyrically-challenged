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
"""Parallel execution pools based on multithreading and multiprocessing.

This module provides 4 types of pools:
- DummyPool: executes work synchronously, in the current process
- ThreadPool: executes work across multiple threads
- ProcessPool: executes work across multiple processes
- HybridPool: executes work across a combination of threads and processes

It also contains a convenience method GetPool to get the appropriate pool for
the given number of threads/processes.

The general usage is as follows:

>>> def identity(value): return value
>>> with parallel.GetPool(num_processes, num_threads) as pool:
...   future = pool.ApplyAsync(identity, (42,))
...   assert future.Get() == 42
...   assert pool.Apply(f, (42,)) == 42
...   map_future = pool.MapAsync(identity, [1, 2, 3])
...   assert map_future.Get() == [1, 2, 3]
...   assert pool.Map(identity, [1, 2, 3]) == [1, 2, 3]

Errors are raised at the time of the Get() call on the future (which is implicit
for Apply() and Map()).
"""
import abc
import multiprocessing
from multiprocessing import pool
import pickle
import Queue
import sys
import threading
import time


################################################################################
# Common Pool Infrastructure
################################################################################


_STOP_WORKING = None  # sentinel value used to tell workers to clean up
_POLL_INTERVAL = 0.01  # in seconds


class InvalidStateException(Exception):
  """Exception to indicate that a parallel pool was put in an invalid state."""

  def __init__(self, msg):
    super(InvalidStateException, self).__init__(msg)


class BasePool(object):
  """Base class for parallel pools.

  Provides a limited subset of the multiprocessing.Pool API.

  Can be used as a context manager:

  >>> with pool:
  ...  assert pool.Map(str, [1, 2, 3]) == ['1', '2', '3']
  """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def Start(self):
    """Initialize non-trivial infrastructure (e.g. processes/threads/queues)."""
    raise NotImplementedError

  @abc.abstractmethod
  def Join(self):
    """Clean up anything started in Start()."""
    raise NotImplementedError

  def Map(self, func, iterable):
    """Applies func to each element in iterable and return a list of results."""
    return self.MapAsync(func, iterable).Get()

  def MapAsync(self, func, iterable):
    """Applies func to each element in iterable and return a future."""
    return _MultiFuture([self.ApplyAsync(func, (arg,)) for arg in iterable])

  def Apply(self, func, args):
    """Applies func to args and returns the result."""
    return self.ApplyAsync(func, args).Get()

  @abc.abstractmethod
  def ApplyAsync(self, func, args):
    """Apply func to args and return a future."""
    raise NotImplementedError

  def __enter__(self):
    self.Start()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.Join()


class BaseFuture(object):
  """A future object containing a value that may not be available yet."""

  __metaclass__ = abc.ABCMeta

  def Get(self):
    return self.GetResult().GetOrRaise()

  @abc.abstractmethod
  def GetResult(self):
    raise NotImplementedError


class _Result(object):
  """Value holder for a result (a value, if successful, or an error).

  Only one of {value, error, exc_info} can be set.

  Both error and exc_info exist due to issues with pickling. exc_info is better,
  because we can re-raise it and preserve the original stacktrace, but it can't
  be pickled. error gets re-raised from GetOrRaise().

  Attributes:
    result: one-tuple of any object (optional), the result of the function. It's
      a one-tuple to distinguish a result of None from no result.
    error: Exception (optional), an exception that was thrown by the function
    exc_info: exc_info (optional) for the exception that occurred
  """

  def __init__(self, value=None, error=None, exc_info=None):
    if sum(map(bool, [value, error, exc_info])) > 1:
      raise ValueError('_Result may only have one of [value, error, exc_info] '
                       'set.')
    if not (value or error or exc_info):
      raise ValueError('_Result must have one of [value, error, exc_info] set.')
    self.value = value
    self.error = error
    self.exc_info = exc_info

  def GetOrRaise(self):
    if self.value:
      return self.value[0]  # self.value is a one-tuple
    elif self.error:
      raise self.error  # pylint: disable=raising-bad-type
    else:
      raise self.exc_info[0], self.exc_info[1], self.exc_info[2]

  def ToPickleableResult(self):
    """Return a pickleable version of this _Result.

    Traceback objects can't be pickled, so we just pass through the exc_value.
    Also, some values and exceptions can't be pickled.

    Returns:
      _Result: a pickleable version of this result.
    """
    if self.exc_info:
      pickleable_result = _Result(error=self.exc_info[1])
    else:
      pickleable_result = self

    try:
      pickle.dumps(pickleable_result)
    except pickle.PicklingError as err:
      return _Result(error=err)
    except Exception as err:  # pylint: disable=broad-except
      return _Result(error=pickle.PicklingError(
          "Couldn't pickle result [{0}]: {1}".format(
              pickleable_result, str(err))))
    return pickleable_result

  def __str__(self):
    return '_Result(value={0}, error={1}, exc_info={2})'.format(
        self.value, self.error, self.exc_info)


class MultiError(Exception):

  def __init__(self, errors):
    self.errors = errors
    super(MultiError, self).__init__(
        'One or more errors occurred:\n' + '\n\n'.join(map(str, errors)))


class _MultiFuture(BaseFuture):
  """Future object that combines other Future objects.

  Returns the results of each future when they are all ready.

  Attributes:
    futures: list of BaseFuture.
  """

  def __init__(self, futures):
    self.futures = futures

  def GetResult(self):
    results = []
    errors = []
    for future in self.futures:
      try:
        results.append(future.Get())
      except Exception as err:  # pylint: disable=broad-except
        errors.append(err)
    if errors:
      return _Result(error=MultiError(errors))
    return _Result(value=(results,))


class _Task(object):
  """An individual work unit to be performed in parallel.

  Attributes:
    func: callable, a function to be called with the given arguments. Must be
      serializable.
    args: tuple, the arguments to pass to func. Must be serializable.
  """

  def __init__(self, func, args):
    self.func = func
    self.args = args

  def __hash__(self):
    return hash((self.func.__name__, self.args))

  def __eq__(self, other):
    return self.func.__name__ == other.func.__name__ and self.args == other.args

  def __ne__(self, other):
    return not self.__eq__(other)


################################################################################
# DummyPool
################################################################################


class _DummyFuture(BaseFuture):

  def __init__(self, result):
    self.result = result

  def GetResult(self):
    return self.result


class DummyPool(BasePool):
  """Serial analog of parallel execution Pool."""

  def __init__(self):
    self._started = False

  def ApplyAsync(self, func, args):
    if not self._started:
      # This is for consistency with the other Pools; if a program works with
      # DummyPool, no changes should be necessary to make it work with the other
      # Pools.
      raise InvalidStateException('DummyPool must be Start()ed before use.')
    try:
      result = _Result((func(*args),))
    except:  # pylint: disable=bare-except
      result = _Result(exc_info=sys.exc_info())
    return _DummyFuture(result)

  def Start(self):
    if self._started:
      raise InvalidStateException('Can only start DummyPool once.')
    self._started = True

  def Join(self):
    if not self._started:
      # This is for consistency with the other Pools; if a program works with
      # DummyPool, no changes should be necessary to make it work with the other
      # Pools.
      raise InvalidStateException('DummyPool must be Start()ed before use.')
    # Do nothing, since there is nothing to clean up

################################################################################
# ProcessPool
################################################################################


class _PoolFutureWrapper(BaseFuture):
  """Wrapper for multiprocessing.Pool.Result (their name for a future)."""

  def __init__(self, result):
    self.result = result

  def GetResult(self):
    try:
      return _Result((self.result.get(),))
    except:  # pylint: disable=bare-except
      return _Result(exc_info=sys.exc_info())


class ProcessPool(BasePool):
  """Process-based parallel execution Pool.

  This object is not thread-safe.
  """

  def __init__(self, num_processes):
    self.num_processes = num_processes
    self._pool = None

  def Start(self):
    if self._pool:
      raise InvalidStateException('Can only start ProcessPool once.')
    self._pool = pool.Pool(self.num_processes)

  def ApplyAsync(self, func, args):
    if not self._pool:
      raise InvalidStateException('ProcessPool must be Start()ed before use.')
    return _PoolFutureWrapper(self._pool.apply_async(func, args))

  def Join(self):
    if not self._pool:
      raise InvalidStateException('ProcessPool must be Start()ed before use.')
    self._pool.close()
    self._pool.join()


################################################################################
# ThreadPool
################################################################################


class _ThreadFuture(BaseFuture):

  def __init__(self, task, results_map):
    self._task = task
    self._results_map = results_map

  def Get(self):
    """Return the value of the future, or raise an exception."""
    return self.GetResult().GetOrRaise()

  def GetResult(self):
    """Get the _Result of the future."""
    while True:
      if self._task in self._results_map:
        return self._results_map[self._task]
      time.sleep(_POLL_INTERVAL)


class _ThreadTask(object):

  def __init__(self, task):
    self.task = task


class _WorkerThread(threading.Thread):

  def __init__(self, work_queue, results_map):
    super(_WorkerThread, self).__init__()
    self.work_queue = work_queue
    self.results_map = results_map

  def run(self):
    while True:
      thread_task = self.work_queue.get()
      if thread_task is _STOP_WORKING:
        return
      task = thread_task.task
      try:
        result = _Result((task.func(*task.args),))
      except:  # pylint: disable=bare-except
        result = _Result(exc_info=sys.exc_info())
      self.results_map[thread_task.task] = result


class ThreadPool(BasePool):
  """Thread-based parallel execution Pool."""

  def __init__(self, num_threads):
    self.num_threads = num_threads
    self._task_queue = Queue.Queue()
    self.worker_threads = []
    self._results_map = {}

  def Start(self):
    if self.worker_threads:
      raise InvalidStateException('ThreadPool must be started at most once.')
    for _ in range(self.num_threads):
      thread = _WorkerThread(self._task_queue, self._results_map)
      self.worker_threads.append(thread)
      thread.start()

  def ApplyAsync(self, func, args):
    if not self.worker_threads:
      raise InvalidStateException('ThreadPool must be Start()ed before use.')
    task = _Task(func, args)
    result = _ThreadFuture(task, self._results_map)
    self._task_queue.put(_ThreadTask(task))
    return result

  def Join(self):
    if not self.worker_threads:
      raise InvalidStateException('ThreadPool must be Start()ed before use.')
    for _ in self.worker_threads:
      self._task_queue.put(_STOP_WORKING)

    for thread in self.worker_threads:
      thread.join()


################################################################################
# HybridPool
################################################################################


def _HybridResultHandler(results, work_queue, result_queue):
  done = False
  while not done or results:
    if not results:
      time.sleep(_POLL_INTERVAL)
      continue
    result = results.pop()
    if result is _STOP_WORKING:
      done = True
      continue
    task, future = result
    result_queue.put((task, future.GetResult().ToPickleableResult()))
    work_queue.task_done()


def _HybridWorkerProcess(work_queue, result_queue, num_threads):
  results = []
  result_handler = threading.Thread(target=_HybridResultHandler,
                                    args=(results, work_queue, result_queue))
  result_handler.start()
  with ThreadPool(num_threads) as thread_pool:
    while True:
      thread_task = work_queue.get()
      if thread_task is _STOP_WORKING:
        results.append(_STOP_WORKING)
        result_handler.join()
        thread_pool.Join()
        work_queue.task_done()
        return
      task = thread_task.task
      try:
        results.append((task, thread_pool.ApplyAsync(task.func, task.args)))
      except pickle.PicklingError:
        results.append((task, _DummyFuture(_Result(exc_info=sys.exc_info()))))


class HybridPool(BasePool):
  """Parallelizes a task using a mix of processes and threads.

  Attributes:
    num_processes: int or None, the number of processes to use
  """

  def __init__(self, num_processes=None, num_threads=None):
    self.num_processes = num_processes
    self.num_threads = num_threads
    self._task_queue = None
    self._manager = None
    self._result_queue = None
    self._results_map = {}
    self._pool = None

  def Start(self):
    if self._pool:
      raise InvalidStateException('HybridPool must be started at most once.')
    self._pool = ProcessPool(self.num_processes)
    self._pool.Start()
    self._manager = multiprocessing.Manager()
    self._task_queue = self._manager.JoinableQueue()
    self._result_queue = self._manager.Queue()
    for _ in range(self.num_processes):
      self._pool.ApplyAsync(
          _HybridWorkerProcess,
          (self._task_queue, self._result_queue, self.num_threads))

    self.results_thread = threading.Thread(target=self._HandleResults)
    self.results_thread.start()

  def Join(self):
    if not self._pool:
      raise InvalidStateException('HybridPool must be Start()ed before use.')
    for _ in range(self.num_processes):
      self._task_queue.put(_STOP_WORKING)
    self._result_queue.put(_STOP_WORKING)

    self._pool.Join()
    self._manager.shutdown()
    self.results_thread.join()

  def _HandleResults(self):
    while True:
      try:
        result = self._result_queue.get()
      except Queue.Empty:
        time.sleep(self._RESULT_TIMEOUT)
        continue
      if result is _STOP_WORKING:
        return
      elif result:
        task, value = result
        self._results_map[task] = value

  def ApplyAsync(self, func, args):
    if not self._pool:
      raise InvalidStateException('HybridPool must be Start()ed before use.')
    task = _Task(func, args)
    result = _ThreadFuture(task, self._results_map)
    self._task_queue.put(_ThreadTask(task))
    return result


################################################################################
# GetPool
################################################################################


def GetPool(num_processes, num_threads):
  """Returns a parallel execution pool for the given thread/process combination.

  Can return any of:
  - DummyPool: if num_processes and num_threads are both 1.
  - ThreadPool: if num_processes is 1
  - ProcessPool: if num_threads is 1.
  - HybridPool: otherwise.

  Args:
    num_processes: int or None, the number of processes to use. If None, default
      to the number of cores on the machine.
    num_threads: int, the number of threads to use.

  Returns:
    BasePool instance appropriate for the given type of parallelism.
  """
  if num_processes is None:
    num_processes = multiprocessing.cpu_count()

  if num_processes == 1 and num_threads == 1:
    return DummyPool()
  elif num_threads == 1:
    return ProcessPool(num_processes)
  elif num_processes == 1:
    return ThreadPool(num_threads)
  else:
    return HybridPool(num_processes, num_threads)
