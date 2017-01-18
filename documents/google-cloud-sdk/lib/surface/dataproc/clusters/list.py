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

"""List cluster command."""
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """View a list of clusters in a project.

  View a list of clusters in a project.

  ## EXAMPLES

  To see the list of all clusters, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, constants.DEFAULT_PAGE_SIZE)

  def Collection(self):
    return 'dataproc.clusters'

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']

    request = self.GetRequest(messages, project, region, args)

    return list_pager.YieldFromList(
        client.projects_regions_clusters,
        request,
        limit=args.limit, field='clusters',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')

  @staticmethod
  def GetRequest(messages, project, region, args):
    return messages.DataprocProjectsRegionsClustersListRequest(
        projectId=project, region=region)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(List):
  """View a list of clusters in a project.

  View a list of clusters in a project. An optional filter can be used to
  constrain the clusters returned. Filters are case-sensitive and have the
  following syntax:

    field = value [AND [field = value]] ...

  where `field` is one of `status.state`, `clusterName`, or `labels.[KEY]`,
  and `[KEY]` is a label key. `value` can be ```*``` to match all values.
  `status.state` can be one of the following: `ACTIVE`, `INACTIVE`,
  `CREATING`, `RUNNING`, `ERROR`, `DELETING`, or `UPDATING`. `ACTIVE`
  contains the `CREATING`, `UPDATING`, and `RUNNING` states. `INACTIVE`
  contains the `DELETING` and `ERROR` states. `clusterName` is the name of the
  cluster provided at creation time. Only the logical `AND` operator is
  supported; space-separated items are treated as having an implicit `AND`
  operator.

  ## EXAMPLES

  To see the list of all clusters, run:

    $ {command}

  To show a cluster whose name is `mycluster`, run:

    $ {command} --filter='clusterName = mycluster'

  To see the list of all clusters with particular labels, run:

    $ {command} --filter='labels.env = staging AND labels.starred = *'

  To see a list of all active clusters with particular labels, run:

    $ {command} --filter='status.state = ACTIVE labels.env = staging AND labels.starred = *'
  """

  @staticmethod
  def GetRequest(messages, project, region, args):
    # Explicitly null out args.filter if present because by default args.filter
    # also acts as a postfilter to the things coming back from the backend
    backend_filter = None
    if args.filter:
      backend_filter = args.filter
      args.filter = None

    return messages.DataprocProjectsRegionsClustersListRequest(
        projectId=project, region=region, filter=backend_filter)
