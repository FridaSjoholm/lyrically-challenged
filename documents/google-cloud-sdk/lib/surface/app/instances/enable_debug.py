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

"""The `app instances enable-debug` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


class EnableDebug(base.Command):
  """Enables debug mode for an instance.

  When in debug mode, SSH will be enabled on the VMs, and you can use
  `gcloud compute ssh` to login to them. They will be removed from the health
  checking pools, but they still receive requests.

  Note that any local changes to an instance will be **lost** if debug mode is
  disabled on the instance. New instance(s) may spawn depending on the app's
  scaling settings.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To enable debug mode for a particular instance, run:

              $ {command} --service=s1 --version=v1 i1

          To enable debug mode for an instance chosen interactively, run:

              $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    instance = parser.add_argument(
        'instance', nargs='?',
        help=('The instance to enable debug mode on.'))
    instance.detailed_help = (
        'The instance ID to enable debug mode on. If not specified, '
        'select instance interactively. Must uniquely specify (with other '
        'flags) exactly one instance')

    service = parser.add_argument(
        '--service', '-s',
        help='Only match instances belonging to this service.')
    service.detailed_help = (
        'If specified, only match instances belonging to the given service. '
        'This affects both interactive and non-interactive selection.')

    version = parser.add_argument(
        '--version', '-v',
        help='Only match instances belonging to this version.')
    version.detailed_help = (
        'If specified, only match instances belonging to the given version. '
        'This affects both interactive and non-interactive selection.')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClient()
    all_instances = api_client.GetAllInstances(
        args.service, args.version,
        version_filter=lambda v: util.Environment.IsFlexible(v.environment))
    try:
      res = resources.REGISTRY.Parse(args.instance)
    except Exception:  # pylint:disable=broad-except
      # If parsing fails, use interactive selection or provided instance ID.
      instance = instances_util.GetMatchingInstance(
          all_instances, service=args.service, version=args.version,
          instance=args.instance)
    else:
      instance = instances_util.GetMatchingInstance(
          all_instances, service=res.servicesId, version=res.versionsId,
          instance=res.instancesId)

    console_io.PromptContinue(
        'About to enable debug mode for instance [{0}].'.format(instance),
        cancel_on_no=True)
    message = 'Enabling debug mode for instance [{0}]'.format(instance)
    res = resources.REGISTRY.Parse(instance.id,
                                   params={'versionsId': instance.version,
                                           'instancesId': instance.id,
                                           'servicesId': instance.service},
                                   collection='appengine.apps.services.'
                                              'versions.instances')
    with progress_tracker.ProgressTracker(message):
      api_client.DebugInstance(res)
