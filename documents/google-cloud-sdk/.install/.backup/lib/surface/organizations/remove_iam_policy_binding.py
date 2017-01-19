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

"""Command to remove IAM policy binding for an organization."""

import httplib

from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.organizations import flags
from googlecloudsdk.command_lib.organizations import orgs_base


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class RemoveIamPolicyBinding(orgs_base.OrganizationCommand):
  """Remove IAM policy binding for an organization.

  Removes a policy binding to the IAM policy of an organization, given an
  organization ID
  and the binding.
  """

  detailed_help = iam_util.GetDetailedHelpForRemoveIamPolicyBinding(
      'organization', 'example-organization-id-1')

  @staticmethod
  def Args(parser):
    flags.IdArg('whose IAM binding you want to remove.').AddToParser(parser)
    iam_util.AddArgsForRemoveIamPolicyBinding(parser)

  @http_retry.RetryOnHttpStatus(httplib.CONFLICT)
  def Run(self, args):
    messages = self.OrganizationsMessages()

    get_policy_request = (
        messages.CloudresourcemanagerOrganizationsGetIamPolicyRequest(
            organizationsId=args.id,
            getIamPolicyRequest=messages.GetIamPolicyRequest()))
    policy = self.OrganizationsClient().GetIamPolicy(get_policy_request)

    iam_util.RemoveBindingFromIamPolicy(policy, args.member, args.role)

    set_policy_request = (
        messages.CloudresourcemanagerOrganizationsSetIamPolicyRequest(
            organizationsId=args.id,
            setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy)))

    return self.OrganizationsClient().SetIamPolicy(set_policy_request)
