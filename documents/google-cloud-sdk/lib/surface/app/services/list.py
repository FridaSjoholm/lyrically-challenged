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
"""`gcloud app services list` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List your existing services.

  This command lists all services that are currently deployed to the App Engine
  server.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list all services in the current project, run:

            $ {command}

          """,
  }

  def Collection(self):
    return 'appengine.services'

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    services = api_client.ListServices()
    versions = api_client.ListVersions(services)

    result = []
    for service in services:
      versions_for_service = [v for v in versions if v.service == service.id]
      result.append(
          {'id': service.id, 'versions': versions_for_service})
    # Sort so the order is deterministic for testing.
    return sorted(result)
