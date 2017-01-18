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

"""Resource formats supplementary help."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_topics


class Formats(base.TopicCommand):
  """Resource formats supplementary help."""

  detailed_help = {

      'DESCRIPTION': textwrap.dedent("""\
          {description}

          ### Formats

          A format expression has 3 parts:

          _NAME_:: _name_
          _ATTRIBUTES_:: *[* [no-]_attribute-name_[=_value_] [, ... ] *]*
          _PROJECTION_:: *(* _resource-key_ [, ...] *)*

          _NAME_ is required, _ATTRIBUTES_ are optional, and _PROJECTIONS_
          may be required for some formats. Unknown attribute names are
          silently ignored.

          Each *gcloud* *list* command has a default format expression. The
          *--format* flag can alter or replace the default. For example,

              --format='[box]'

          adds box decorations to a default table, and

              --format=json

          lists the resource in *json* format.

          {format_registry}
          """).format(
              description=resource_topics.ResourceDescription('format'),
              format_registry=resource_topics.FormatRegistryDescriptions()),

      'EXAMPLES': """\
          List a table of compute instance resources sorted by *name* with
          box decorations and title *Instances*:

            $ gcloud compute instances list --format='table[box,title=Instances](name:sort=1, zone:title=zone, status)'

          List the disk interfaces for all compute instances as a compact
          comma separated list:

            $ gcloud compute instances list --format='value(disks[].interface.list())'

          List the URIs for all compute instances:

            $ gcloud compute instances list --format='value(uri())'

          List the project authenticated user email address:

            $ gcloud info --format='value(config.account)'
          """,
      }
