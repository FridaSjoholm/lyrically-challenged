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

"""Command to remove a principal from a service's access policy."""

import httplib

from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.service_management import common_flags


class RemoveIamPolicyBinding(base.Command):
  """Removes an IAM policy binding from a service's access policy."""

  detailed_help = iam_util.GetDetailedHelpForRemoveIamPolicyBinding(
      'service', 'my-service')

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    service_flag = common_flags.producer_service_flag(
        suffix='from which the member is to be removed')
    service_flag.AddToParser(parser)

    iam_util.AddArgsForRemoveIamPolicyBinding(parser)

  @http_retry.RetryOnHttpStatus(httplib.CONFLICT)
  def Run(self, args):
    """Run 'service-management remove-iam-policy-binding'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the access API call.

    Raises:
      ToolException: An error such as specifying a label that doesn't exist
        or a principal that is already a member of the service or visibility
        label.
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()
    request = messages.ServicemanagementServicesGetIamPolicyRequest(
        servicesId=args.service)

    policy = client.services.GetIamPolicy(request)

    iam_util.RemoveBindingFromIamPolicy(
        policy, args.member, args.role)

    # Send updated access policy to backend
    request = messages.ServicemanagementServicesSetIamPolicyRequest(
        servicesId=args.service,
        setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy))
    return client.services.SetIamPolicy(request)
