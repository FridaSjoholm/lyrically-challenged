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

"""The runtime-configs variables describe command."""

from googlecloudsdk.api_lib.deployment_manager.runtime_configs import util
from googlecloudsdk.command_lib.deployment_manager.runtime_configs import base_commands


class Describe(base_commands.VariableRetrieverCommand):
  """Describe variable resources.

  This command displays information about the variable resource with the
  specified name.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To describe a variable named "my-var", run:

            $ {command} --config-name my-config my-var
          """,
  }

  def Run(self, args):
    result = super(Describe, self).Run(args)
    return util.FormatVariable(result)
