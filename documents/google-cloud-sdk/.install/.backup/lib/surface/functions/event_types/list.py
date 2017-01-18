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
"""The event-types command subgroup for Google Cloud Functions.

'functions event-types list' command.
"""
from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """Describes the allowed values and meanings of --trigger-* flags.

  Prints the table with list of all ways to deploy an event trigger. When using
  `gcloud functions deploy` Event Providers are specified as
  --trigger-provider and Event Types are specified as --trigger-event.
  The table includes the type of resource expected in
  --trigger-resource and whether the --trigger-path parameter is optional,
  required, or disallowed.

  * For an event type, EVENT_TYPE_DEFAULT marks whether the given event type is
    the default for its provider (in which case the --event-type flag may be
    omitted).
  * For a resource, RESOURCE_OPTIONAL marks whether the resource has a
    corresponding default value (in which case the --trigger-resource flag
    may be omitted).
  """

  def Format(self, args):
    return '''\
        table(provider.label:label="EVENT_PROVIDER":sort=1,
              label:label="EVENT_TYPE":sort=2,
              event_is_optional.yesno('Yes'):label="EVENT_TYPE_DEFAULT",
              resource_type.value.name:label="RESOURCE_TYPE",
              resource_is_optional.yesno('Yes'):label="RESOURCE_OPTIONAL",
              path_obligatoriness.name:label="PATH_PARAMETER"
        )'''

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      All event types.
    """
    for provider in util.trigger_provider_registry.providers:
      for event in provider.events:
        yield event
