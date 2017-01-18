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

"""The `app instances describe` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Describe(base.Command):
  """Display all data about an existing instance."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To show all data about instance i1 for service s1 and version v1, run:

              $ {command} --service=s1 --version=v1 i1
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'instance',
        help='The instance ID.')
    parser.add_argument(
        '--service', '-s', required=True,
        help='The service ID.')
    parser.add_argument(
        '--version', '-v', required=True,
        help='The version ID.')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    params = {'servicesId': args.service,
              'versionsId': args.version}
    res = resources.REGISTRY.Parse(args.instance,
                                   params=params,
                                   collection='appengine.apps.services.'
                                              'versions.instances')
    return api_client.GetInstanceResource(res)
