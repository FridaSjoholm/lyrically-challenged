# Copyright 2014 Google Inc. All Rights Reserved.
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

"""The command-group for the Updater service CLI."""

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import store


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Updater(base.Group):
  """Manage updates in a managed instance group."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--zone', help='Rolling update zone name.',
        action=actions.StoreProperty(properties.VALUES.compute.zone))

  @exceptions.RaiseToolExceptionInsteadOf(store.Error)
  def Filter(self, context, args):
    """Context() is a filter function that can update the context.

    Args:
      context: The current context.
      args: The argparse namespace that was specified on the CLI or API.

    Returns:
      The updated context.
    """
    properties.VALUES.compute.zone.Get(required=True)
    resources.REGISTRY.SetParamDefault(
        api='compute', collection=None, param='project',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.REGISTRY.SetParamDefault(
        api='compute', collection=None, param='zone',
        resolver=resolvers.FromProperty(properties.VALUES.compute.zone))
    resources.REGISTRY.SetParamDefault(
        api='replicapoolupdater', collection=None, param='project',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.REGISTRY.SetParamDefault(
        api='replicapoolupdater', collection=None, param='zone',
        resolver=resolvers.FromProperty(properties.VALUES.compute.zone))
    return context
