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
"""Utilities for dealing with ML models API."""

from apitools.base.py import list_pager
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _ParseModel(model_id):
  return resources.REGISTRY.Parse(model_id, collection='ml.projects.models')


class ModelsClient(object):
  """High-level client for the ML models surface."""

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance('ml', 'v1beta1')
    self.messages = messages or apis.GetMessagesModule('ml', 'v1beta1')

  def Create(self, model):
    """Create a new model."""
    model_ref = _ParseModel(model)
    req = self.messages.MlProjectsModelsCreateRequest(
        projectsId=model_ref.projectsId,
        googleCloudMlV1beta1Model=self.messages.GoogleCloudMlV1beta1Model(
            name=model_ref.Name()))
    return self.client.projects_models.Create(req)

  def Delete(self, model):
    """Delete an existing model."""
    model_ref = _ParseModel(model)
    req = self.messages.MlProjectsModelsDeleteRequest(
        projectsId=model_ref.projectsId, modelsId=model_ref.Name())
    return self.client.projects_models.Delete(req)

  def Get(self, model):
    """Get details about a model."""
    model_ref = _ParseModel(model)
    req = self.messages.MlProjectsModelsGetRequest(
        projectsId=model_ref.projectsId, modelsId=model_ref.Name())
    return self.client.projects_models.Get(req)

  def List(self):
    """List models in the project."""
    req = self.messages.MlProjectsModelsListRequest(
        projectsId=properties.VALUES.core.project.Get())
    return list_pager.YieldFromList(
        self.client.projects_models,
        req,
        field='models',
        batch_size_attribute='pageSize')
