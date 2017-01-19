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
"""Helper methods for constructing messages for the container CLI."""

from googlecloudsdk.calliope import exceptions


def AutoUpdateUpgradeRepairMessage(value, flag_name):
  """Messaging for when auto-upgrades or node auto-repairs.

  Args:
    value: bool, value that the flag takes.
    flag_name: str, the name of the flag. Must be either autoupgrade or
        autorepair

  Returns:
    the formatted message string.
  """
  action = 'enable' if value else 'disable'
  if flag_name != 'autoupgrade' and flag_name != 'autorepair':
    raise exceptions.InvalidArgumentException(
        'Invalid value for flag_name: ' + flag_name +
        '. Must be either autorepair or autoupgrade')
  plural = flag_name + 's'
  return ('This will {0} the {1} feature for nodes. Please see\n'
          'https://cloud.google.com/container-engine/docs/'
          'node-management for more\n'
          'information on node {2}.\n').format(action, flag_name, plural)
