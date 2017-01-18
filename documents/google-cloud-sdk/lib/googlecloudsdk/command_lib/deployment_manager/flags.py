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

"""Helper methods for configuring deployment manager command flags."""

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import arg_parsers


def AddDeploymentNameFlag(parser):
  """Add properties flag."""
  parser.add_argument('deployment_name', help='Deployment name.')


def AddPropertiesFlag(parser):
  """Add properties flag."""

  parser.add_argument(
      '--properties',
      help='A comma seperated, key=value, map '
      'to be used when deploying a template file directly.',
      type=arg_parsers.ArgDict(operators=dm_v2_util.NewParserDict()),
      dest='properties')


def AddAsyncFlag(parser):
  """Add the async argument."""
  parser.add_argument(
      '--async',
      help='Return immediately and print information about the Operation in '
      'progress rather than waiting for the Operation to complete. '
      '(default=False)',
      dest='async',
      default=False,
      action='store_true')


def AddDeletePolicyFlag(parser, request_class):
  """Add the delete_policy argument."""
  parser.add_argument(
      '--delete-policy',
      help=('Delete policy for resources that will change as part of an update '
            'or delete. DELETE deletes the resource while ABANDON just removes '
            'the resource reference from the deployment.'),
      default='DELETE',
      choices=(sorted(request_class.DeletePolicyValueValuesEnum
                      .to_dict().keys())))
