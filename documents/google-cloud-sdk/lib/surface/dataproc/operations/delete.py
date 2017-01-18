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

"""Delete operation command."""
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete the record of an inactive operation.

  Delete the record of an inactive operation.

  ## EXAMPLES

  To delete the record of an operation, run:

    $ {command} operation_id
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('operation', help='The ID of the operation to delete.')

  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    operation_ref = util.ParseOperation(args.operation, self.context)

    request = messages.DataprocProjectsRegionsOperationsDeleteRequest(
        name=operation_ref.RelativeName())

    console_io.PromptContinue(
        message="The operation '{0}' will be deleted.".format(args.operation),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.')

    client.projects_regions_operations.Delete(request)

    # TODO(user) Check that operation was deleted.

    log.DeletedResource(args.operation)
