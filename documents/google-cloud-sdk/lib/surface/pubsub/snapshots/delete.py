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
"""Cloud Pub/Sub snapshots delete command."""

from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """This feature is part of an invite-only release of the Cloud Pub/Sub API.

  Deletes one or more Cloud Pub/Sub snapshots.
  This feature is part of an invitation-only release of the underlying
  Cloud Pub/Sub API. The command will generate errors unless you have access to
  this API. This restriction should be relaxed in the near future. Please
  contact cloud-pubsub@google.com with any questions in the meantime.
  """

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""

    parser.add_argument('snapshot', nargs='+',
                        help='One or more snapshot names to delete.')

  def Collection(self):
    return util.SNAPSHOTS_COLLECTION

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.snapshots'.
    """
    msgs = self.context['pubsub_msgs']
    pubsub = self.context['pubsub']

    for snapshot_name in args.snapshot:
      snapshot_path = util.SnapshotFormat(snapshot_name)
      delete_req = msgs.PubsubProjectsSnapshotsDeleteRequest(
          snapshot=snapshot_path)

      try:
        pubsub.projects_snapshots.Delete(delete_req)
        failed = None
      except api_ex.HttpError as error:
        exc = exceptions.HttpException(error)
        failed = exc.payload.status_message

      result = util.SnapshotDisplayDict(
          msgs.Snapshot(name=snapshot_path), failed)
      log.DeletedResource(snapshot_path, kind='snapshot', failed=failed)
      yield result
