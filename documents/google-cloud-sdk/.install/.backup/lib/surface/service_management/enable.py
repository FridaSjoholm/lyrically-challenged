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

"""service-management enable command."""

from googlecloudsdk.api_lib.service_management import enable_api
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_management import common_flags
from googlecloudsdk.core import properties


class Enable(base.SilentCommand):
  """Enables a service on the current project.

  Enables a service on the current project.

  More information on enabling a service can be found at:
  https://cloud.google.com/service-management/enable-disable#enabling_services
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.available_service_flag(suffix='to enable').AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'service-management enable'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.
    """
    project = properties.VALUES.core.project.Get(required=True)
    operation = enable_api.EnableServiceApiCall(project, args.service)
    return services_util.ProcessOperationResult(operation, args.async)
