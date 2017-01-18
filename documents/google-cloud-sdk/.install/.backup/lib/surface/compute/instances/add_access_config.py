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
"""Command for adding access configs to virtual machine instances."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


class AddAccessConfigInstances(base_classes.NoOutputAsyncMutator):
  """Create a Google Compute Engine virtual machine access configuration.

  *{command}* is used to create access configurations for network
  interfaces of Google Compute Engine virtual machines.
  """

  @staticmethod
  def Args(parser):
    access_config_name = parser.add_argument(
        '--access-config-name',
        default=constants.DEFAULT_ACCESS_CONFIG_NAME,
        help='Specifies the name of the new access configuration.')
    access_config_name.detailed_help = """\
        Specifies the name of the new access configuration. ``{0}''
        is used as the default if this flag is not provided.
        """.format(constants.DEFAULT_ACCESS_CONFIG_NAME)

    address = parser.add_argument(
        '--address',
        action=arg_parsers.StoreOnceAction,
        help=('Specifies the external IP address of the new access '
              'configuration.'))
    address.detailed_help = """\
        Specifies the external IP address of the new access
        configuration. If this is not specified, then the service will
        choose an available ephemeral IP address. If an explicit IP
        address is given, then that IP address must be reserved by the
        project and not be in use by another resource.
        """

    network_interface = parser.add_argument(
        '--network-interface',
        default='nic0',
        action=arg_parsers.StoreOnceAction,
        help=('Specifies the name of the network interface on which to add '
              'the new access configuration.'))
    network_interface.detailed_help = """\
        Specifies the name of the network interface on which to add the new
        access configuration. If this is not provided, then "nic0" is used
        as the default.
        """

    instance_flags.INSTANCE_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'AddAccessConfig'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    """Returns a list of request necessary for adding an access config."""
    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=compute_flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    request = self.messages.ComputeInstancesAddAccessConfigRequest(
        accessConfig=self.messages.AccessConfig(
            name=args.access_config_name,
            natIP=args.address,
            type=self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT),
        instance=instance_ref.Name(),
        networkInterface=args.network_interface,
        project=self.project,
        zone=instance_ref.zone)

    return [request]
