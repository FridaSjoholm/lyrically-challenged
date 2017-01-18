# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Base exceptions for the Cloud SDK."""

import os

from googlecloudsdk.core.util import platforms


class _Error(Exception):
  """A base exception for all Cloud SDK errors.

  This exception should not be used directly.
  """
  pass


class InternalError(_Error):
  """A base class for all non-recoverable internal errors."""
  pass


class Error(_Error):
  """A base exception for all user recoverable errors.

  Any exception that extends this class will not be printed with a stack trace
  when running from CLI mode.  Instead it will be shows with a message of how
  the user can correct this problem.

  All exceptions of this type must have a message for the user.
  """

  def __init__(self, *args, **kwargs):
    """Initialize a core.Error.

    Args:
      *args: positional args for exceptions.
      **kwargs: keyword args for exceptions, and additional arguments:
        - exit_code: int, The desired exit code for the CLI.
    """
    super(Error, self).__init__(*args)
    self.exit_code = kwargs.get('exit_code', 1)


class MultiError(Error):
  """Collection of Error instances as single exception."""

  def __init__(self, errors):
    super(MultiError, self).__init__(', '.join(str(e) for e in errors))


class RequiresAdminRightsError(Error):
  """An exception for when you don't have permission to modify the SDK.

  This tells the user how to run their command with administrator rights so that
  they can perform the operation.
  """

  def __init__(self, sdk_root):
    message = (
        u'You cannot perform this action because you do not have permission '
        u'to modify the Google Cloud SDK installation directory [{root}].\n\n'
        .format(root=sdk_root))
    if (platforms.OperatingSystem.Current() ==
        platforms.OperatingSystem.WINDOWS):
      message += (
          'Click the Google Cloud SDK Shell icon and re-run the command in '
          'that window, or re-run the command with elevated privileges by '
          'right-clicking cmd.exe and selecting "Run as Administrator".')
    else:
      # Specify the full path because sudo often uses secure_path and won't
      # respect the user's $PATH settings.
      gcloud_path = os.path.join(sdk_root, 'bin', 'gcloud')
      message += (
          u'Re-run the command with sudo: sudo {0} ...'.format(gcloud_path))
    super(RequiresAdminRightsError, self).__init__(message)


class NetworkIssueError(Error):
  """An error to wrap a general network issue."""

  def __init__(self, message):
    super(NetworkIssueError, self).__init__(
        '{message}\n'
        'This may be due to network connectivity issues. Please check your '
        'network settings, and the status of the service you are trying to '
        'reach.'.format(message=message))
