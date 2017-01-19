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
"""Command for setting IAM policies for service accounts."""

from googlecloudsdk.command_lib.iam import base_classes
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base_classes.BaseIamCommand):
  """Set the IAM policy for a service account.

  This command replaces the existing IAM policy for a service account, given
  an IAM-ACCOUNT and a file encoded in JSON or YAML that contains the IAM
  policy. If the given policy file specifies an "etag" value, then the
  replacement will succeed only if the policy already in place matches that
  etag. (An etag obtained via $ gcloud iam service-accounts get-iam-policy will
  prevent the replacement if the policy for the service account has been
  subsequently updated.) A policy file that does not contain an etag value will
  replace any existing policy for the service account.
  """

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy(
      'service account', 'my-iam-account@somedomain.com')

  @staticmethod
  def Args(parser):
    parser.add_argument('account',
                        metavar='IAM-ACCOUNT',
                        help='The service account whose policy to '
                        'set.')
    parser.add_argument(
        'policy_file',
        metavar='POLICY-FILE',
        help='Path to a local JSON or YAML formatted file '
        'containing a valid policy.')

  def Run(self, args):
    policy = iam_util.ParsePolicyFile(args.policy_file, self.messages.Policy)

    return self.iam_client.projects_serviceAccounts.SetIamPolicy(
        self.messages.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=iam_util.EmailToAccountResourceName(args.account),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)))
