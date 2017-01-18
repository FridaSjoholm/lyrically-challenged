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

"""'functions locations list' command."""

import sys
from apitools.base.py import exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as base_exceptions
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """Returns a list of locations where functions can be deployed."""

  def Collection(self):
    return 'functions.projects.locations'

  def Run(self, args):
    client = self.context['functions_client']
    list_generator = list_pager.YieldFromList(
        service=client.projects_locations,
        request=self.BuildRequest(args),
        field='locations', batch_size_attribute='pageSize')
    try:
      for item in list_generator:
        yield item
    except exceptions.HttpError as error:
      msg = util.GetHttpErrorMessage(error)
      unused_type, unused_value, traceback = sys.exc_info()
      raise base_exceptions.HttpException, msg, traceback

  def BuildRequest(self, args):
    messages = self.context['functions_messages']
    project = properties.VALUES.core.project.Get(required=True)
    return messages.CloudfunctionsProjectsLocationsListRequest(
        name='projects/' + project,
    )
