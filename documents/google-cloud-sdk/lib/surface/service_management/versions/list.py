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

"""service-management versions list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.service_management import services_util

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class List(base.ListCommand):
  """Lists the configurations for a given service.

  DEPRECATED: This command is deprecated and will be removed.
  Use 'gcloud beta service-management configs list' instead.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--service',
                        required=True,
                        help='The service to describe.')

  def Run(self, args):
    """Run 'service-management versions list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the List API call.
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    request = messages.ServicemanagementServicesConfigsListRequest(
        serviceName=args.service)

    log.status.Print('Available configuration versions for service \'%s\':'
                     % args.service)

    return list_pager.YieldFromList(
        client.services_configs,
        request,
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='serviceConfigs')

  def Collection(self):
    return 'servicemanagement-v1.serviceConfigs'
