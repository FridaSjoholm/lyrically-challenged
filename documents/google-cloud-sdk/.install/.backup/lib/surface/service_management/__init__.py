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

"""The command group for the ServiceManagement V1 CLI."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class ServiceManagement(base.Group):
  """Create, enable, or otherwise manage API services."""

  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    Raises:
      ToolException: When no project is specified.
    """

    context['servicemanagement-v1'] = apis.GetClientInstance(
        'servicemanagement', 'v1')
    context['servicemanagement-v1-messages'] = apis.GetMessagesModule(
        'servicemanagement', 'v1')

    context['apikeys-v1'] = apis.GetClientInstance('apikeys', 'v1')
    context['apikeys-v1-messages'] = apis.GetMessagesModule(
        'apikeys', 'v1')

    return context
