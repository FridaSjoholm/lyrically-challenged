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

"""Error support for Cloud Debugger libraries."""

from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import exceptions


class DebugError(exceptions.Error):
  pass


class NoEndpointError(DebugError):

  def __str__(self):
    return (
        'Debug endpoint not initialized. DebugObject.InitializeApiClients must '
        'be called before using this module.\n')


class BreakpointNotFoundError(DebugError):

  def __init__(self, breakpoint_ids, type_name):
    super(BreakpointNotFoundError, self).__init__(
        '{0} ID not found: {1}'.format(type_name.capitalize(),
                                       ', '.join(breakpoint_ids)))


class UnknownHttpError(api_exceptions.HttpException, DebugError):
  """An unknown error occurred during a remote API call."""

  def __init__(self, error):
    super(UnknownHttpError, self).__init__(error)


class MultipleDebuggeesError(DebugError):
  """Multiple targets matched the search criteria."""

  def __init__(self, pattern, debuggees):
    if pattern:
      pattern_msg = ' matching "{0}"'.format(pattern)
    else:
      pattern_msg = ''
    super(MultipleDebuggeesError, self).__init__(
        'Multiple possible targets found{0}.\n'
        'Use the --target option to select one of the following '
        'targets:\n    {1}\n'.format(
            pattern_msg, '\n    '.join([d.name for d in debuggees])))


class NoMatchError(DebugError):
  """No object matched the search criteria."""

  def __init__(self, object_type, pattern=None):
    if pattern:
      super(NoMatchError, self).__init__(
          'No {0} matched the pattern "{1}"'.format(object_type, pattern))
    else:
      super(NoMatchError, self).__init__(
          'No {0} was found for this project.'.format(object_type))


class NoDebuggeeError(DebugError):
  """No debug target matched the search criteria."""

  def __init__(self, pattern=None, debuggees=None):
    if pattern:
      msg = 'No active debug target matched the pattern "{0}"\n'.format(pattern)
    else:
      msg = 'No active debug targets were found for this project.\n'
    if debuggees:
      msg += (
          'Use the --target option to select one of the following '
          'targets:\n    {0}\n'.format(
              '\n    '.join([d.name for d in debuggees])))
    super(NoDebuggeeError, self).__init__(msg)
