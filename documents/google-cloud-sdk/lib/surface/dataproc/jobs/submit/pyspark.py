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

"""Submit a PySpark job to a cluster."""

import argparse

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class PySpark(base_classes.JobSubmitter):
  """Submit a PySpark job to a cluster.

  Submit a PySpark job to a cluster.

  ## EXAMPLES
  To submit a PySpark job with a local script, run:

    $ {command} --cluster my_cluster my_script.py

  To submit a Spark job that runs a script that is already on the cluster, run:

    $ {command} --cluster my_cluster file:///usr/lib/spark/examples/src/main/python/pi.py 100
  """

  @staticmethod
  def Args(parser):
    super(PySpark, PySpark).Args(parser)
    PySparkBase.Args(parser)

  def ConfigureJob(self, job, args):
    PySparkBase.ConfigureJob(
        self.context['dataproc_messages'],
        job,
        self.BuildLoggingConfig(args.driver_log_levels),
        self.files_by_type,
        args)

  def PopulateFilesByType(self, args):
    self.files_by_type.update(PySparkBase.GetFilesByType(args))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class PySparkBeta(base_classes.JobSubmitterBeta):
  """Submit a PySpark job to a cluster.

  Submit a PySpark job to a cluster.

  ## EXAMPLES
  To submit a PySpark job with a local script, run:

    $ {command} --cluster my_cluster my_script.py

  To submit a Spark job that runs a script that is already on the cluster, run:

    $ {command} --cluster my_cluster file:///usr/lib/spark/examples/src/main/python/pi.py 100
  """

  @staticmethod
  def Args(parser):
    super(PySparkBeta, PySparkBeta).Args(parser)
    PySparkBase.Args(parser)

  def ConfigureJob(self, job, args):
    PySparkBase.ConfigureJob(
        self.context['dataproc_messages'],
        job,
        self.BuildLoggingConfig(args.driver_log_levels),
        self.files_by_type,
        args)
    # Apply labels
    super(PySparkBeta, self).ConfigureJob(job, args)

  def PopulateFilesByType(self, args):
    self.files_by_type.update(PySparkBase.GetFilesByType(args))


class PySparkBase(object):
  """Submit a PySpark job to a cluster."""

  @staticmethod
  def Args(parser):
    """Performs command-line argument parsing specific to PySpark."""

    parser.add_argument(
        'py_file',
        help='The main .py file to run as the driver.')
    parser.add_argument(
        '--py-files',
        type=arg_parsers.ArgList(),
        metavar='PY_FILE',
        default=[],
        help=('Comma separated list of Python files to be provided to the job.'
              'Must be one of the following file formats" .py, ,.zip, or .egg'))
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=('Comma separated list of jar files to be provided to the '
              'executor and driver classpaths.'))
    parser.add_argument(
        '--files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        default=[],
        help='Comma separated list of files to be provided to the job.')
    parser.add_argument(
        '--archives',
        type=arg_parsers.ArgList(),
        metavar='ARCHIVE',
        default=[],
        help=('Comma separated list of archives to be provided to the job. '
              'must be one of the following file formats: .zip, .tar, .tar.gz, '
              'or .tgz.'))
    parser.add_argument(
        'job_args',
        nargs=argparse.REMAINDER,
        help='The arguments to pass to the driver.')
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help='A list of key value pairs to configure PySpark.')
    parser.add_argument(
        '--driver-log-levels',
        type=arg_parsers.ArgDict(),
        metavar='PACKAGE=LEVEL',
        help=('A list of package to log4j log level pairs to configure driver '
              'logging. For example: root=FATAL,com.example=INFO'))

  @staticmethod
  def GetFilesByType(args):
    # TODO(user): Move arg manipulation elsewhere.
    return {
        'py_file': args.py_file,
        'py_files': args.py_files,
        'archives': args.archives,
        'files': args.files,
        'jars': args.jars}

  @staticmethod
  def ConfigureJob(messages, job, log_config, files_by_type, args):
    """Populates the pysparkJob member of the given job."""

    pyspark_job = messages.PySparkJob(
        args=args.job_args,
        archiveUris=files_by_type['archives'],
        fileUris=files_by_type['files'],
        jarFileUris=files_by_type['jars'],
        pythonFileUris=files_by_type['py_files'],
        mainPythonFileUri=files_by_type['py_file'],
        loggingConfig=log_config)

    if args.properties:
      pyspark_job.properties = encoding.DictToMessage(
          args.properties, messages.PySparkJob.PropertiesValue)

    job.pysparkJob = pyspark_job

PySpark.detailed_help = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
      To submit a PySpark job with a local script, run:

        $ {command} --cluster my_cluster my_script.py

      To submit a Spark job that runs a script that is already on the \
  cluster, run:

        $ {command} --cluster my_cluster file:///usr/lib/spark/examples/src/main/python/pi.py 100
      """,
}
PySparkBeta.detailed_help = PySpark.detailed_help
