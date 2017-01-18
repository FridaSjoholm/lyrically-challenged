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
"""Provides common arguments for the ML command surface."""
import argparse
import itertools
import sys

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class ArgumentError(exceptions.Error):
  pass


# Run flags
DISTRIBUTED = base.Argument(
    '--distributed',
    action='store_true',
    default=False,
    help=('Runs the provided code in distributed mode by providing cluster '
          'configurations as environment variables to subprocesses'))
PARAM_SERVERS = base.Argument(
    '--parameter-server-count',
    type=int,
    help=('Number of parameter servers with which to run. '
          'Ignored if --distributed is not specified. Default: 2'))
WORKERS = base.Argument(
    '--worker-count',
    type=int,
    help=('Number of workers with which to run. '
          'Ignored if --distributed is not specified. Default: 2'))
START_PORT = base.Argument(
    '--start-port',
    type=int,
    default=27182,
    help='Start of the range of ports reserved by the local cluster.',
    detailed_help="""\
Start of the range of ports reserved by the local cluster. This command will use
a contiguous block of ports equal to parameter-server-count + worker-count + 1.

If --distributed is not specified, this flag is ignored.
""")


# TODO(user): move these into a class
CONFIG = base.Argument(
    '--config',
    help='Path to yaml configuration file.',
    # TODO(b/33456372): add prediction and training config file examples.
    detailed_help="""\
Path to the job configuration file. The file should be a yaml document
containing a Job resource as defined in the API:
https://cloud.google.com/ml/reference/rest/v1beta1/projects.jobs
""")
JOB_NAME = base.Argument('job', help='Name of the job.')
MODULE_NAME = base.Argument(
    '--module-name',
    required=True,
    help='Name of the module to run')
PACKAGE_PATH = base.Argument(
    '--package-path',
    help='Path to a Python package to build')
PACKAGES = base.Argument(
    '--packages',
    # TODO(b/33234717) remove nargs=+ after deprecation period
    nargs='+',
    default=[],
    type=arg_parsers.ArgList(),
    metavar='PACKAGE',
    help='Path to Python archives used for training')
USER_ARGS = base.Argument(
    'user_args',
    nargs=argparse.REMAINDER,
    help='Additional user arguments to be fowarded to user code')
VERSION_NAME = base.Argument('version', help='Name of the model version.')
VERSION_DATA = base.Argument(
    '--origin',
    required=True,
    help='Location containing the model graph.',
    detailed_help="""\
Location of ```model/``` "directory" (as output by
https://www.tensorflow.org/versions/r0.12/api_docs/python/state_ops.html#Saver).

Can be a Google Cloud Storage (`gs://`) path or local file path (no prefix). In
the latter case the files will be uploaded to Google Cloud Storage and a
`--staging-bucket` argument is required.
""")
_SCALE_TIER_CHOICES = {
    'BASIC': ('A single worker instance. This tier is suitable for learning '
              'how to use Cloud ML, and for experimenting with new models '
              'using small datasets.'),
    'STANDARD_1': 'Many workers and a few parameter servers.',
    'PREMIUM_1': 'A large number of workers with many parameter servers.',
    'CUSTOM': """\
The CUSTOM tier is not a set tier, but rather enables you to use your own
cluster specification. When you use this tier, set values to configure your
processing cluster according to these guidelines (using the --config flag):

* You _must_ set `TrainingInput.masterType` to specify the type of machine to
  use for your master node. This is the only required setting.
* You _may_ set `TrainingInput.workerCount` to specify the number of workers to
  use. If you specify one or more workers, you _must_ also set
  `TrainingInput.workerType` to specify the type of machine to use for your
  worker nodes.
* You _may_ set `TrainingInput.parameterServerCount` to specify the number of
  parameter servers to use. If you specify one or more parameter servers, you
  _must_ also set `TrainingInput.parameterServerType` to specify the type of
  machine to use for your parameter servers.  Note that all of your workers must
  use the same machine type, which can be different from your parameter server
  type and master type. Your parameter servers must likewise use the same
  machine type, which can be different from your worker type and master type.\
"""}
SCALE_TIER = base.Argument(
    '--scale-tier',
    help=('Specifies the machine types, the number of replicas for workers and '
          'parameter servers.'),
    choices=_SCALE_TIER_CHOICES,
    default=None)

POLLING_INTERVAL = base.Argument(
    '--polling-interval',
    type=arg_parsers.BoundedInt(1, sys.maxint, unlimited=True),
    required=False,
    default=60,
    help='Number of seconds to wait between efforts to fetch the latest '
    'log messages.')
ALLOW_MULTILINE_LOGS = base.Argument(
    '--allow-multiline-logs',
    action='store_true',
    help='Output multiline log messages as single records.')
TASK_NAME = base.Argument(
    '--task-name',
    required=False,
    default=None,
    help='If set, display only the logs for this particular task.')


def GetModelName(positional=True, required=False):
  help_text = 'Name of the model.'
  if positional:
    return base.Argument('model', help=help_text)
  else:
    return base.Argument('--model', help=help_text, required=required)


# TODO(b/33234717): remove after PACKAGES nargs=+ deprecation period.
def ProcessPackages(args):
  """Flatten PACKAGES flag and warn if multiple arguments were used."""
  if args.packages is not None:
    if len(args.packages) > 1:
      log.warn('Use of --packages with space separated values is '
               'deprecated and will not work in the future. Use comma '
               'instead.')
    # flatten packages into a single list
    args.packages = list(itertools.chain.from_iterable(args.packages))


def GetStagingBucket(required):
  return base.Argument(
      '--staging-bucket',
      help='Bucket in which to stage training archives',
      type=storage_util.BucketReference.FromArgument,
      required=required)
