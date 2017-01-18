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

"""Describe operation command."""
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """View the details of an operation.

  View the details of an operation.

  ## EXAMPLES

  To view the details of an operation, run:

    $ {command} operation_id
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'operation', help='The ID of the operation to describe.')

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    operation_ref = util.ParseOperation(args.operation, self.context)

    request = messages.DataprocProjectsRegionsOperationsGetRequest(
        name=operation_ref.RelativeName())

    operation = client.projects_regions_operations.Get(request)
    return operation
