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

"""Upgrade cluster command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import text
from googlecloudsdk.core.util.semver import SemVer


class UpgradeHelpText(object):
  """Upgrade available help text messages."""
  UPGRADE_AVAILABLE = '''
* - There is an upgrade available for your cluster(s).
'''

  SUPPORT_ENDING = '''
** - The current version of your cluster(s) will soon be out of support, please upgrade.
'''

  UNSUPPORTED = '''
*** - The current version of your cluster(s) is unsupported, please upgrade.
'''

  UPGRADE_COMMAND = '''
To upgrade nodes to the latest available version, run
  $ gcloud container clusters upgrade {name}'''


class VersionVerifier(object):
  """Compares the cluster and master versions for upgrade availablity."""
  UP_TO_DATE = 0
  UPGRADE_AVAILABLE = 1
  SUPPORT_ENDING = 2
  UNSUPPORTED = 3

  def Compare(self, current_master_version, current_cluster_version):
    """Compares the cluster and master versions and returns an enum."""
    # TODO(user):update the if condition when we roll the master version
    if current_master_version == current_cluster_version:
      return self.UP_TO_DATE
    master_version = SemVer(current_master_version)
    cluster_version = SemVer(current_cluster_version)
    major, minor, _ = master_version.Distance(cluster_version)
    if major != 0 or minor > 2:
      return self.UNSUPPORTED
    elif minor > 1:
      return self.SUPPORT_ENDING
    else:
      return self.UPGRADE_AVAILABLE


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'name',
      metavar='NAME',
      help='The name of the cluster to upgrade.')
  cv = flags.AddClusterVersionFlag(parser, 'master or nodes')
  cv.detailed_help = """\
    The Kubernetes release version to which to upgrade the cluster's nodes.

    If provided, the --cluster-version must be no greater than the cluster
    master's minor version (x.*X*.x), and must be a latest patch version
    (x.x.*X*).

    You can find the list of allowed versions for upgrades by running:

      $ gcloud container get-server-config
  """
  parser.add_argument(
      '--node-pool',
      help='The node pool to upgrade.')
  parser.add_argument(
      '--master',
      help='Upgrade the cluster\'s master to the latest version of Kubernetes'
      ' supported on Container Engine. Nodes cannot be upgraded at the same'
      ' time as the master.',
      action='store_true')
  flags.AddClustersWaitAndAsyncFlags(parser)
  flags.AddImageTypeFlag(parser, 'cluster/node pool')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Upgrade(base.Command):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']

    cluster_ref = adapter.ParseCluster(args.name)

    # Make sure it exists (will raise appropriate error if not)
    cluster = adapter.GetCluster(cluster_ref)

    options = api_adapter.UpdateClusterOptions(
        version=args.cluster_version,
        update_master=args.master,
        update_nodes=(not args.master),
        node_pool=args.node_pool,
        image_type=args.image_type)

    if options.version:
      new_version = options.version
    else:
      new_version = 'latest'

    if args.master:
      node_message = 'Master'
      current_version = cluster.currentMasterVersion
    else:
      node_message = 'All {node_count} {node}'.format(
          node_count=cluster.currentNodeCount,
          node=text.Pluralize(cluster.currentNodeCount, 'node'))
      current_version = cluster.currentNodeVersion

    console_io.PromptContinue(
        message=
        '{node_message} of cluster [{cluster_name}] will be upgraded '
        'from version [{current_version}] to version [{new_version}]. '
        'This operation is long-running and will block other operations '
        'on the cluster (including delete) until it has run to completion.'
        .format(node_message=node_message,
                cluster_name=cluster.name,
                current_version=current_version,
                new_version=new_version),
        throw_if_unattended=True,
        cancel_on_no=True)

    try:
      op_ref = adapter.UpdateCluster(cluster_ref, options)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    if not flags.GetAsyncValueFromAsyncAndWaitFlags(args.async, args.wait):
      adapter.WaitForOperation(
          op_ref, 'Upgrading {0}'.format(cluster_ref.clusterId))

      log.UpdatedResource(cluster_ref)

Upgrade.detailed_help = {
    'DESCRIPTION': """\
      Upgrades the Kubernetes version of an existing container cluster.

      This command upgrades the Kubernetes version of the *nodes* of a cluster.
      The Kubernetes version of the cluster's *master* is periodically upgraded
      automatically as new releases are available.

      *By running this command, all of the cluster's nodes will be deleted and*
      *recreated one at a time.* While persistent Kubernetes resources, such as
      pods backed by replication controllers, will be rescheduled onto new nodes,
      a small cluster may experience a few minutes where there are insufficient
      nodes available to run all of the scheduled Kubernetes resources.

      *Please ensure that any data you wish to keep is stored on a persistent*
      *disk before upgrading the cluster.* Ephemeral Kubernetes resources--in
      particular, pods without replication controllers--will be lost, while
      persistent Kubernetes resources will get rescheduled.
    """,
    'EXAMPLES': """\
      Upgrade the nodes of <cluster> to the Kubernetes version of the cluster's
      master.

        $ {command} <cluster>

      Upgrade the nodes of <cluster> to Kubernetes version x.y.z.

        $ {command} <cluster> --cluster-version "x.y.z"
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpgradeBeta(Upgrade):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpgradeAlpha(Upgrade):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
