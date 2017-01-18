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

"""service-management configs describe command."""

from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_management import completion_callbacks


class Describe(base.DescribeCommand):
  """Describes the configuration for a given version of a service."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    callback = completion_callbacks.ProducerServiceFlagCompletionCallback
    parser.add_argument('--service',
                        required=True,
                        completion_resource=services_util.SERVICES_COLLECTION,
                        list_command_callback_fn=callback,
                        help='The service from which to retrieve the '
                             'configuration.')

    parser.add_argument('config_id',
                        help='The configuration ID to retrieve.')

  def Run(self, args):
    """Run 'service-management configs describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Get API call.
    """

    # Check if the user wants the active config or a specific config.
    return self._GetConfig(args.service, args.config_id)

  def Collection(self):
    return services_util.CONFIG_COLLECTION

  def _GetConfig(self, service, config_id):
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    request = messages.ServicemanagementServicesConfigsGetRequest(
        serviceName=service, configId=config_id)
    return client.services_configs.Get(request)
