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

"""Describe cluster command."""

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """View the details of a cluster."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To view the details of a cluster, run:

            $ {command} my_cluster
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the cluster to describe.')

  def Run(self, args):
    client = self.context['dataproc_client']

    cluster_ref = util.ParseCluster(args.name, self.context)
    request = client.MESSAGES_MODULE.DataprocProjectsRegionsClustersGetRequest(
        projectId=cluster_ref.projectId,
        region=cluster_ref.region,
        clusterName=cluster_ref.clusterName)

    cluster = client.projects_regions_clusters.Get(request)
    return cluster
