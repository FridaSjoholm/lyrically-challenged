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

"""Implements the command for SSHing into an instance."""
import argparse
import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.util import gaia
from googlecloudsdk.command_lib.util import ssh
from googlecloudsdk.core.util import platforms


def _Args(parser):
  """Argument parsing for ssh, including hook for remote completion."""
  ssh_utils.BaseSSHCLICommand.Args(parser)

  command = parser.add_argument(
      '--command',
      help='A command to run on the virtual machine.')
  command.detailed_help = """\
      A command to run on the virtual machine.

      Runs the command on the target instance and then exits.
      """

  ssh_flags = parser.add_argument(
      '--ssh-flag',
      action='append',
      help='Additional flags to be passed to ssh.')
  ssh_flags.detailed_help = """\
      Additional flags to be passed to *ssh(1)*. It is recommended that flags
      be passed using an assignment operator and quotes. This flag will
      replace occurences of ``%USER%'' and ``%INSTANCE%'' with their
      dereferenced values. Example:

        $ {command} example-instance --zone us-central1-a --ssh-flag="-vvv" --ssh-flag="-L 80:%INSTANCE%:80"

      is equivalent to passing the flags ``--vvv'' and ``-L
      80:162.222.181.197:80'' to *ssh(1)* if the external IP address of
      'example-instance' is 162.222.181.197.
      """

  parser.add_argument(
      '--container',
      help="""\
          The name of a container inside of the virtual machine instance to
          connect to. This only applies to virtual machines that are using
          a Google container virtual machine image. For more information,
          see [](https://cloud.google.com/compute/docs/containers)
          """)

  user_host = parser.add_argument(
      'user_host',
      completion_resource='compute.instances',
      help='Specifies the instance to SSH into.',
      metavar='[USER@]INSTANCE')

  user_host.detailed_help = """\
      Specifies the instance to SSH into.

      ``USER'' specifies the username with which to SSH. If omitted,
      $USER from the environment is selected.
      """

  parser.add_argument(
      'ssh_args',
      nargs=argparse.REMAINDER,
      help="""\
          Flags and positionals passed to the underlying ssh implementation.
          """,
      example="""\
        $ {command} example-instance --zone us-central1-a -- -vvv -L 80:%INSTANCE%:80
      """)

  flags.AddZoneFlag(
      parser,
      resource_type='instance',
      operation_type='connect to')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SshGA(ssh_utils.BaseSSHCLICommand):
  """SSH into a virtual machine instance."""

  def __init__(self, *args, **kwargs):
    super(SshGA, self).__init__(*args, **kwargs)
    self._use_accounts_service = False

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    super(SshGA, self).Run(args)

    parts = args.user_host.split('@')
    if len(parts) == 1:
      if self._use_accounts_service:  # Using Account Service.
        user = gaia.GetDefaultAccountName(self.http)
      else:  # Uploading keys through metadata.
        user = ssh.GetDefaultSshUsername(warn_on_account_user=True)
      instance = parts[0]
    elif len(parts) == 2:
      user, instance = parts
    else:
      raise exceptions.ToolException(
          'Expected argument of the form [USER@]INSTANCE; received [{0}].'
          .format(args.user_host))

    instance_ref = instance_flags.SSH_INSTANCE_RESOLVER.ResolveResources(
        [instance], compute_scope.ScopeEnum.ZONE, args.zone, self.resources,
        scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))[0]
    instance = self.GetInstance(instance_ref)
    external_ip_address = ssh_utils.GetExternalIPAddress(instance)

    ssh_args = [self.ssh_executable]
    if not args.plain:
      ssh_args.extend(self.GetDefaultFlags())
      # Allocates a tty if no command was provided and a container was provided.
      if args.container and not args.command:
        ssh_args.append('-t')

    if args.ssh_flag:
      for flag in args.ssh_flag:
        for flag_part in flag.split():  # We want grouping here
          dereferenced_flag = (
              flag_part.replace('%USER%', user)
              .replace('%INSTANCE%', external_ip_address))
          ssh_args.append(dereferenced_flag)

    host_key_alias = self.HostKeyAlias(instance)
    ssh_args.extend(self.GetHostKeyArgs(args, host_key_alias))

    ssh_args.append(ssh.UserHost(user, external_ip_address))

    if args.ssh_args:
      ssh_args.extend(args.ssh_args)
    if args.container:
      ssh_args.append('--')
      ssh_args.append('container_exec')
      ssh_args.append(args.container)
      # Runs the given command inside the given container if --command was
      # specified, otherwise runs /bin/sh.
      if args.command:
        ssh_args.append(args.command)
      else:
        ssh_args.append('/bin/sh')

    elif args.command:
      if not platforms.OperatingSystem.IsWindows():
        ssh_args.append('--')
      ssh_args.append(args.command)

    # Don't use strict error checking for ssh: if the executed command fails, we
    # don't want to consider it an error. We do, however, want to propagate its
    # return code.
    return_code = self.ActuallyRun(
        args, ssh_args, user, instance, instance_ref.project,
        strict_error_checking=False,
        use_account_service=self._use_accounts_service)
    if return_code:
      # Can't raise an exception because we don't want any "ERROR" message
      # printed; the output from `ssh` will be enough.
      sys.exit(return_code)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SshBeta(SshGA):
  """SSH into a virtual machine instance."""

  def __init__(self, *args, **kwargs):
    super(SshBeta, self).__init__(*args, **kwargs)
    self._use_accounts_service = True

  @staticmethod
  def Args(parser):
    _Args(parser)


def DetailedHelp(version):
  """Construct help text based on the command release track."""
  detailed_help = {
      'brief': 'SSH into a virtual machine instance',
      'DESCRIPTION': """\
        *{command}* is a thin wrapper around the *ssh(1)* command that
        takes care of authentication and the translation of the
        instance name into an IP address.

        This command ensures that the user's public SSH key is present
        in the project's metadata. If the user does not have a public
        SSH key, one is generated using *ssh-keygen(1)* (if the `--quiet`
        flag is given, the generated key will have an empty passphrase).
        """,
      'EXAMPLES': """\
        To SSH into 'example-instance' in zone ``us-central1-a'', run:

          $ {command} example-instance --zone us-central1-a

        You can also run a command on the virtual machine. For
        example, to get a snapshot of the guest's process tree, run:

          $ {command} example-instance --zone us-central1-a --command "ps -ejH"

        If you are using the Google container virtual machine image, you
        can SSH into one of your containers with:

          $ {command} example-instance --zone us-central1-a --container CONTAINER
        """,
  }
  if version == 'BETA':
    detailed_help['DESCRIPTION'] = """\
        *{command}* is a thin wrapper around the *ssh(1)* command that
        takes care of authentication and the translation of the
        instance name into an IP address.

        This command uses the Compute Accounts API to ensure that the user's
        public SSH key is availibe to the VM. This form of key management
        will only work with VMs configured to work with the Compute Accounts
        API. If the user does not have a public SSH key, one is generated using
        *ssh-keygen(1)* (if `the --quiet` flag is given, the generated key will
        have an empty passphrase).

        """
  return detailed_help

SshGA.detailed_help = DetailedHelp('GA')
SshBeta.detailed_help = DetailedHelp('BETA')
