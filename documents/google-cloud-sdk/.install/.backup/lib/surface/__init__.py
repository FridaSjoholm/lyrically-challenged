# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The super-group for the cloud CLI."""

import argparse
import os
import textwrap

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Gcloud(base.Group):
  """Manage Google Cloud Platform resources and developer workflow.

  The *gcloud* CLI manages authentication, local configuration, developer
  workflow, and interactions with the Google Cloud Platform APIs.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--account',
        metavar='ACCOUNT',
        category=base.COMMONLY_USED_FLAGS,
        help='Google Cloud Platform user account to use for invocation.',
        action=actions.StoreProperty(properties.VALUES.core.account))

    project_arg = parser.add_argument(
        '--project',
        metavar='PROJECT_ID',
        dest='project',
        category=base.COMMONLY_USED_FLAGS,
        suggestion_aliases=['--application'],
        completion_resource='cloudresourcemanager.projects',
        list_command_path='beta.projects',
        help='Google Cloud Platform project ID to use for this invocation.',
        action=actions.StoreProperty(properties.VALUES.core.project))

    project_arg.detailed_help = """\
        The Google Cloud Platform project name to use for this invocation. If
        omitted then the current project is assumed.
        """
    # Must have a None default so properties are not always overridden when the
    # arg is not provided.
    quiet_arg = parser.add_argument(
        '--quiet',
        '-q',
        default=None,
        category=base.COMMONLY_USED_FLAGS,
        help='Disable all interactive prompts.',
        action=actions.StoreConstProperty(
            properties.VALUES.core.disable_prompts, True))
    quiet_arg.detailed_help = """\
        Disable all interactive prompts when running gcloud commands. If input
        is required, defaults will be used, or an error will be raised.
        """

    trace_group = parser.add_mutually_exclusive_group()
    trace_group.add_argument(
        '--trace-token',
        default=None,
        action=actions.StoreProperty(properties.VALUES.core.trace_token),
        help='Token used to route traces of service requests for investigation'
        ' of issues.')
    trace_group.add_argument(
        '--trace-email',
        metavar='USERNAME',
        default=None,
        action=actions.StoreProperty(properties.VALUES.core.trace_email),
        help=argparse.SUPPRESS)
    trace_group.add_argument(
        '--trace-log',
        default=None,
        action=actions.StoreBooleanProperty(properties.VALUES.core.trace_log),
        help=argparse.SUPPRESS)
