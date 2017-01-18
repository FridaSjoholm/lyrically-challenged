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

"""Common flags for projects commands."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util


def GetProjectFlag(verb):
  return base.Argument(
      'id',
      metavar='PROJECT_ID',
      completion_resource=util.PROJECTS_COLLECTION,
      list_command_path='projects',
      help='ID for the project you want to {0}.'.format(verb))
