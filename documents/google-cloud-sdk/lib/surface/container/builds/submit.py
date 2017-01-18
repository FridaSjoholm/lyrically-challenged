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
"""Submit build command."""

import os.path

from apitools.base.py import encoding

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import config
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import times


_ALLOWED_SOURCE_EXT = ['.zip', '.tgz', '.gz']


class FailedBuildException(core_exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, status):
    super(FailedBuildException, self).__init__(
        'build completed with status "{status}"'.format(status=status))


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA)
class Submit(base.CreateCommand):
  """Submit a build using the Google Container Builder service."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        'source',
        help='The source directory on local disk or tarball in Google Cloud '
             'Storage or disk to use for this build.',
    )
    parser.add_argument(
        '--gcs-source-staging-dir',
        help='Directory in Google Cloud Storage to stage a copy of the source '
             'used for the build. If the bucket does not exist, it will be '
             'created. If not set, gs://<project id>_cloudbuild/source is '
             'used.',
    )
    parser.add_argument(
        '--gcs-log-dir',
        help='Directory in Google Cloud Storage to hold build logs. If the '
             'bucket does not exist, it will be created. If not set, '
             'gs://<project id>_cloudbuild/logs is used.',
    )
    parser.add_argument(
        '--timeout',
        help='Maximum time a build can last before it is failed as "TIMEOUT", '
             'written as a duration (eg "2h15m5s" is two hours, fifteen '
             'minutes, and five seconds). If no unit is specified, seconds is '
             'assumed (eg "10" is 10 seconds).',
        action=actions.StoreProperty(properties.VALUES.container.build_timeout),
    )
    build_config = parser.add_mutually_exclusive_group(required=True)
    build_config.add_argument(
        '--tag', '-t',
        help='The tag to use with a "docker build" image creation. The '
             'Container Builder service will run a remote "docker build -t '
             '$TAG .", where $TAG is the tag provided by this flag. The tag '
             'must be in the gcr.io/* or *.gcr.io/* namespaces.',
    )
    build_config.add_argument(
        '--config',
        help='The .yaml or .json file to use for build configuration.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedBuildException: If the build is completed and not 'SUCCESS'.
    """

    project = properties.VALUES.core.project.Get()
    safe_project = project.replace(':', '_')
    safe_project = safe_project.replace('.', '_')
    # The string 'google' is not allowed in bucket names.
    safe_project = safe_project.replace('google', 'elgoog')

    default_bucket_name = '{}_cloudbuild'.format(safe_project)

    default_gcs_source = False
    if args.gcs_source_staging_dir is None:
      default_gcs_source = True
      args.gcs_source_staging_dir = 'gs://{}/source'.format(default_bucket_name)

    default_gcs_log_dir = False
    if args.gcs_log_dir is None:
      default_gcs_log_dir = True
      args.gcs_log_dir = 'gs://{}/logs'.format(default_bucket_name)

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()
    registry = self.context['registry']

    gcs_client = storage_api.StorageClient()

    # First, create the build request.
    build_timeout = properties.VALUES.container.build_timeout.Get()

    if build_timeout is not None:
      try:
        # A bare number is interpreted as seconds.
        build_timeout_secs = int(build_timeout)
      except ValueError:
        build_timeout_duration = times.ParseDuration(build_timeout)
        build_timeout_secs = int(build_timeout_duration.total_seconds)
      timeout_str = str(build_timeout_secs) + 's'
    else:
      timeout_str = None

    if args.tag:
      if 'gcr.io/' not in args.tag:
        raise c_exceptions.InvalidArgumentException(
            '--tag',
            'Tag value must be in the gcr.io/* or *.gcr.io/* namespace.')
      build_config = messages.Build(
          images=[args.tag],
          steps=[
              messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=['build', '--no-cache', '-t', args.tag, '.'],
              ),
          ],
          timeout=timeout_str,
      )
    elif args.config:
      build_config = config.LoadCloudbuildConfig(args.config, messages)

    if build_config.timeout is None:
      build_config.timeout = timeout_str

    suffix = '.tgz'
    if args.source.startswith('gs://') or os.path.isfile(args.source):
      _, suffix = os.path.splitext(args.source)

    # Next, stage the source to Cloud Storage.
    staged_object = '{stamp}_{tag_ish}{suffix}'.format(
        stamp=times.GetTimeStampFromDateTime(times.Now()),
        tag_ish='_'.join(build_config.images or ['null']).replace('/', '_'),
        suffix=suffix,
    )
    gcs_source_staging_dir = registry.Parse(
        args.gcs_source_staging_dir, collection='storage.objects')

    # We first try to create the bucket, before doing all the checks, in order
    # to avoid a race condition. If we do the check first, an attacker could
    # be lucky enough to create the bucket after the check and before this
    # bucket creation.
    gcs_client.CreateBucketIfNotExists(gcs_source_staging_dir.bucket)

    # If no bucket is specified (for the source `default_gcs_source` or for the
    # logs `default_gcs_log_dir`), check that the default bucket is also owned
    # by the project (b/33046325).
    if default_gcs_source or default_gcs_log_dir:
      # This request returns only the buckets owned by the project.
      bucket_list_req = gcs_client.messages.StorageBucketsListRequest(
          project=project,
          prefix=default_bucket_name)
      bucket_list = gcs_client.client.buckets.List(bucket_list_req)
      found_bucket = False
      for bucket in bucket_list.items:
        if bucket.id == default_bucket_name:
          found_bucket = True
          break
      if not found_bucket:
        if default_gcs_source:
          raise c_exceptions.RequiredArgumentException(
              'gcs_source_staging_dir',
              'A bucket with name {} already exists and is owned by '
              'another project. Specify a bucket using '
              '--gcs_source_staging_dir.'.format(default_bucket_name))
        elif default_gcs_log_dir:
          raise c_exceptions.RequiredArgumentException(
              'gcs-log-dir',
              'A bucket with name {} already exists and is owned by '
              'another project. Specify a bucket to hold build logs '
              'using --gcs-log-dir.'.format(default_bucket_name))

    if gcs_source_staging_dir.object:
      staged_object = gcs_source_staging_dir.object + '/' + staged_object

    gcs_source_staging = registry.Create(
        collection='storage.objects',
        bucket=gcs_source_staging_dir.bucket,
        object=staged_object)

    if args.source.startswith('gs://'):
      gcs_source = registry.Parse(
          args.source, collection='storage.objects')
      staged_source_obj = gcs_client.Rewrite(gcs_source, gcs_source_staging)
      build_config.source = messages.Source(
          storageSource=messages.StorageSource(
              bucket=staged_source_obj.bucket,
              object=staged_source_obj.name,
              generation=staged_source_obj.generation,
          ))
    else:
      if not os.path.exists(args.source):
        raise c_exceptions.BadFileException(
            'could not find source [{src}]'.format(src=args.source))
      if os.path.isdir(args.source):
        source_snapshot = snapshot.Snapshot(args.source)
        size_str = resource_transform.TransformSize(
            source_snapshot.uncompressed_size)
        log.status.Print(
            'Creating temporary tarball archive of {num_files} file(s)'
            ' totalling {size} before compression.'.format(
                num_files=len(source_snapshot.files),
                size=size_str))
        staged_source_obj = source_snapshot.CopyTarballToGCS(
            gcs_client, gcs_source_staging)
        build_config.source = messages.Source(
            storageSource=messages.StorageSource(
                bucket=staged_source_obj.bucket,
                object=staged_source_obj.name,
                generation=staged_source_obj.generation,
            ))
      elif os.path.isfile(args.source):
        unused_root, ext = os.path.splitext(args.source)
        if ext not in _ALLOWED_SOURCE_EXT:
          raise c_exceptions.BadFileException(
              'Local file [{src}] is none of '+', '.join(_ALLOWED_SOURCE_EXT))
        log.status.Print(
            'Uploading local file [{src}] to '
            '[gs://{bucket}/{object}].'.format(
                src=args.source,
                bucket=gcs_source_staging.bucket,
                object=gcs_source_staging.object,
            ))
        staged_source_obj = gcs_client.CopyFileToGCS(
            storage_util.BucketReference.FromBucketUrl(
                gcs_source_staging.bucket),
            args.source, gcs_source_staging.object)
        build_config.source = messages.Source(
            storageSource=messages.StorageSource(
                bucket=staged_source_obj.bucket,
                object=staged_source_obj.name,
                generation=staged_source_obj.generation,
            ))

    gcs_log_dir = registry.Parse(
        args.gcs_log_dir, collection='storage.objects')

    if gcs_log_dir.bucket != gcs_source_staging.bucket:
      # Create the logs bucket if it does not yet exist.
      gcs_client.CreateBucketIfNotExists(gcs_log_dir.bucket)
    build_config.logsBucket = 'gs://'+gcs_log_dir.bucket+'/'+gcs_log_dir.object

    log.debug('submitting build: '+repr(build_config))

    # Start the build.
    op = client.projects_builds.Create(
        messages.CloudbuildProjectsBuildsCreateRequest(
            build=build_config,
            projectId=properties.VALUES.core.project.Get()))
    json = encoding.MessageToJson(op.metadata)
    build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

    build_ref = registry.Create(
        collection='cloudbuild.projects.builds',
        projectId=build.projectId,
        id=build.id)

    log.CreatedResource(build_ref)
    if build.logUrl:
      log.status.Print('Logs are permanently available at [{log_url}].'.format(
          log_url=build.logUrl))
    else:
      log.status.Print('Logs are available in the Cloud Console.')

    # If the command is run --async, we just print out a reference to the build.
    if args.async:
      return build

    def _CancelBuildHandler(unused_signal_number, unused_stack_frame):
      log.status.Print('Cancelling...')
      client.projects_builds.Cancel(
          messages.CloudbuildProjectsBuildsCancelRequest(
              projectId=build_ref.projectId,
              id=build_ref.id))
      log.status.Print('Cancelled [{r}].'.format(r=str(build_ref)))

    # Otherwise, logs are streamed from GCS.
    with execution_utils.CtrlCSection(_CancelBuildHandler):
      build = cb_logs.CloudBuildClient(client, messages).Stream(build_ref)

    if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
      log.status.Print(
          'Your build timed out. Use the [--timeout=DURATION] flag to change '
          'the timeout threshold.')

    if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
      raise FailedBuildException(build.status)

    return build

  def Collection(self):
    return 'cloudbuild.projects.builds'

  def Format(self, args):
    return self.ListFormat(args)
