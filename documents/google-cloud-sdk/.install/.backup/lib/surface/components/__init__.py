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

"""The super-group for the update manager."""

import argparse
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Components(base.Group):
  """List, install, update, or remove Google Cloud SDK components."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Because you might need only some of the tools in the Cloud SDK to do
          your work, you can control which tools are installed on your
          workstation. You can install new tools on your workstation when you
          find that you need them, and remove tools that you no longer need.
          The gcloud command regularly checks whether updates are available for
          the tools you already have installed, and gives you the opportunity
          to upgrade to the latest version.

          Certain components _depend_ on other components. When you install a
          component that you need, all components upon which it directly or
          indirectly depends, and that are not already present on your
          workstation, are installed automatically. When you remove a
          component, all components that depend on the removed component are
          also removed.
      """,
      'EXAMPLES': """\
          To see all available components:

            $ {command} list

          To install a component you don't have:

            $ {command} install COMPONENT

          To remove a component you no longer need:

            $ {command} remove COMPONENT

          To update all components you have to their latest version:

            $ {command} update

          To update all installed components to version 1.2.3:

            $ {command} update --version 1.2.3
      """,
  }

  @staticmethod
  def Args(parser):
    """Sets args for gcloud components."""
    # An override for the location to install components into.
    parser.add_argument('--sdk-root-override', required=False,
                        help=argparse.SUPPRESS)
    # A different URL to look at instead of the default.
    parser.add_argument('--snapshot-url-override', required=False,
                        help=argparse.SUPPRESS)
    # This is not a commonly used option.  You can use this flag to create a
    # Cloud SDK install for an OS other than the one you are running on.
    # Running the updater multiple times for different operating systems could
    # result in an inconsistent install.
    parser.add_argument('--operating-system-override', required=False,
                        help=argparse.SUPPRESS)
    # This is not a commonly used option.  You can use this flag to create a
    # Cloud SDK install for a processor architecture other than that of your
    # current machine.  Running the updater multiple times for different
    # architectures could result in an inconsistent install.
    parser.add_argument('--architecture-override', required=False,
                        help=argparse.SUPPRESS)

  # pylint:disable=g-missing-docstring
  def Filter(self, unused_tool_context, args):

    if config.INSTALLATION_CONFIG.IsAlternateReleaseChannel():
      log.warning('You are using alternate release channel: [%s]',
                  config.INSTALLATION_CONFIG.release_channel)
      # Always show the URL if using a non standard release channel.
      log.warning('Snapshot URL for this release channel is: [%s]',
                  config.INSTALLATION_CONFIG.snapshot_url)
