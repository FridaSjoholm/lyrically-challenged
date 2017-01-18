# Copyright 2014 Google Inc. All Rights Reserved.
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

"""The main command group for myservice.

Everything under here will be the commands in your group.  Each file results in
a command with that name.

This module contains a single class that extends base.Group.  Calliope will
dynamically search for the implementing class and use that as the command group
for this command tree.  You can implement methods in this class to override some
of the default behavior.
"""

import argparse

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources as cloud_resources


SERVICE_NAME = 'dataflow'

DATAFLOW_MESSAGES_MODULE_KEY = 'dataflow_messages'
DATAFLOW_APITOOLS_CLIENT_KEY = 'dataflow_client'
DATAFLOW_REGISTRY_KEY = 'dataflow_registry'


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Dataflow(base.Group):
  """Read and manipulate Google Dataflow resources.
  """

  def Filter(self, context, args):
    """Setup the API client within the context for this group's commands.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.
    """
    cloud_resources.REGISTRY.SetParamDefault(
        api='dataflow', collection=None, param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DataflowDeprecated(base.Group):
  """Read and manipulate Google Dataflow resources.
  """

  def __init__(self):
    log.warn('The Dataflow Alpha CLI is now deprecated and will soon be '
             'removed. Please use the new `gcloud beta dataflow` commands.')

  def Filter(self, context, args):
    """Setup the API client within the context for this group's commands.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.
    """
    cloud_resources.REGISTRY.SetParamDefault(
        api='dataflow', collection=None, param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
