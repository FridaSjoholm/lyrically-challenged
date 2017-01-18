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

"""The `app services describe` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import exceptions as api_lib_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base.Command):
  """Display all data about an existing service."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To show all the data about the current application, run

              $ {command}
          """,
  }

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    try:
      return api_client.GetApplication()
    except api_lib_exceptions.NotFoundError:
      log.debug('No app found:', exc_info=True)
      project = api_client.project
      raise exceptions.MissingApplicationError(project)
