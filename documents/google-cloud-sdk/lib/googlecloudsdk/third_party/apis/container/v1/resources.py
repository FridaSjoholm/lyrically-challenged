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
"""Resource definitions for cloud platform apis."""

import enum


BASE_URL = 'https://container.googleapis.com/v1/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS_ZONES_CLUSTERS = (
      'projects.zones.clusters',
      'projects/{projectId}/zones/{zone}/clusters/{clusterId}',
      {},
      [u'projectId', u'zone', u'clusterId']
  )
  PROJECTS_ZONES_CLUSTERS_NODEPOOLS = (
      'projects.zones.clusters.nodePools',
      'projects/{projectId}/zones/{zone}/clusters/{clusterId}/nodePools/'
      '{nodePoolId}',
      {},
      [u'projectId', u'zone', u'clusterId', u'nodePoolId']
  )
  PROJECTS_ZONES_OPERATIONS = (
      'projects.zones.operations',
      'projects/{projectId}/zones/{zone}/operations/{operationId}',
      {},
      [u'projectId', u'zone', u'operationId']
  )

  def __init__(self, collection_name, path, flat_paths, params):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
