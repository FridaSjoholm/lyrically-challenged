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
"""Command for to list all of a project's service accounts."""

from apitools.base.py import list_pager

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import base_classes
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties


class List(base_classes.BaseIamCommand, base.ListCommand):
  """List all of a project's service accounts."""

  def Collection(self):
    return 'iam.service_accounts'

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    if args.limit is not None:
      if args.limit < 1:
        raise exceptions.ToolException('Limit size must be >=1')

    project = properties.VALUES.core.project.Get(required=True)
    for item in list_pager.YieldFromList(
        self.iam_client.projects_serviceAccounts,
        self.messages.IamProjectsServiceAccountsListRequest(
            name=iam_util.ProjectToProjectResourceName(project)),
        field='accounts',
        limit=args.limit,
        batch_size_attribute='pageSize'):
      yield item
