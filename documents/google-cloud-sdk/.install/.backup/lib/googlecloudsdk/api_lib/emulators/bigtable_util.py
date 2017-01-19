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
"""Utility functions for gcloud bigtable emulator."""

import os
from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log

BIGTABLE = 'bigtable'
BIGTABLE_TITLE = 'Google Cloud Bigtable emulator'
BIGTABLE_EXECUTABLE = 'cbtemulator'


def GetDataDir():
  return util.GetDataDir(BIGTABLE)


def BuildStartArgs(args):
  """Builds the command for starting the bigtable emulator.

  Args:
    args: (list of str) The arguments for the bigtable emulator, excluding the
      program binary.

  Returns:
    A list of command arguments.
  """
  bigtable_dir = util.GetEmulatorRoot(BIGTABLE)
  bigtable_executable = os.path.join(bigtable_dir,
                                     BIGTABLE_EXECUTABLE)
  return execution_utils.ArgsForExecutableTool(bigtable_executable, *args)


def GetEnv(args):
  """Returns an environment variable mapping from an argparse.Namespace."""
  return {'BIGTABLE_EMULATOR_HOST': '%s:%s' %
                                    (args.host_port.host, args.host_port.port)}


def Start(args):
  bigtable_args = BuildStartArgs(util.BuildArgsList(args))
  log.status.Print('Executing: {0}'.format(' '.join(bigtable_args)))
  bigtable_process = util.Exec(bigtable_args)
  util.WriteEnvYaml(GetEnv(args), GetDataDir())
  util.PrefixOutput(bigtable_process, BIGTABLE)
