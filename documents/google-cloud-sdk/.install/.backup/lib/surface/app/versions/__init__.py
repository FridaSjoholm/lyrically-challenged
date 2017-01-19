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

"""The gcloud app versions group."""
from googlecloudsdk.calliope import base


class Versions(base.Group):
  """View and manage your App Engine versions.

  This set of commands can be used to view and manage your existing App Engine
  versions.

  To create new deployments, use `{parent_command} deploy`.

  For more information on App Engine versions, see:
  https://cloud.google.com/appengine/docs/python/an-overview-of-app-engine

  ## EXAMPLES

  To list your deployed versions, run:

    $ {command} list
  """
