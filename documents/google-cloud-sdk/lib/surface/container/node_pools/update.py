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
"""Update node pool command."""
import argparse

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.command_lib.container import messages
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* updates a node pool in a Google Container Engine cluster.
        """,
    'EXAMPLES': """\
        To turn on node auto repair in "node-pool-1" in the cluster
        "sample-cluster", run:

          $ {command} node-pool-1 --cluster=example-cluster --enable-autoupgrade
        """,
}


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument('name', help='The name of the node pool to update.')
  parser.add_argument(
      '--cluster',
      help='The cluster this node pool belongs to.',
      action=actions.StoreProperty(properties.VALUES.container.cluster))
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      help=argparse.SUPPRESS)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Updates a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, suppressed=True)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True)

  def ParseUpdateNodePoolOptions(self, args):
    return api_adapter.UpdateNodePoolOptions(
        enable_autorepair=args.enable_autorepair,
        enable_autoupgrade=args.enable_autoupgrade)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully updated node pool.

    Raises:
      util.Error, if creation failed.
    """
    adapter = api_adapter.NewAPIAdapter()
    pool_ref = adapter.ParseNodePool(args.name)
    options = self.ParseUpdateNodePoolOptions(args)
    if options.enable_autorepair is None and options.enable_autoupgrade is None:
      exceptions.RequiredArgumentException(
          'You must provide --[no-]enable-autoupgrade or '
          '--[no-]enable_autorepair')
      return None

    if options.enable_autorepair is not None:
      log.status.Print(messages.AutoUpdateUpgradeRepairMessage(
          options.enable_autorepair, 'autorepair'))

    if options.enable_autoupgrade is not None:
      log.status.Print(messages.AutoUpdateUpgradeRepairMessage(
          options.enable_autoupgrade, 'autoupgrade'))
    try:
      operation_ref = adapter.UpdateNodePool(pool_ref, options)

      adapter.WaitForOperation(
          operation_ref,
          'Updating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.UpdatedResource(pool_ref)
    return pool

  def Collection(self):
    return 'container.projects.zones.clusters.nodePools'

  def Format(self, args):
    return self.ListFormat(args)

Update.detailed_help = DETAILED_HELP
