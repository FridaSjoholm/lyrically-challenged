# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Resource projections supplementary help."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_topics


class Projections(base.TopicCommand):
  """Resource projections supplementary help."""

  detailed_help = {

      # pylint: disable=protected-access, need transform dicts.
      'DESCRIPTION': textwrap.dedent("""\
          {description}

          ### Projections

          A projection is a list of keys that selects resource data values.
          Projections are used in *--format* flag expressions. For example, the
          *table* format requires a projection that describes the table columns:

            table(name, network.ip.internal, network.ip.external, uri())

          ### Transforms

          A *transform* formats resource data values. Each projection key may
          have zero or more transform calls:

            _key_._transform_([arg...])...

          This example applies the *foo*() and then the *bar*() transform to the
          *status.time* resource value:

            (name, status.time.foo().bar())

          {transform_registry}

          ### Key Attributes

          Key attributes control formatted output. Each projection key may have
          zero or more attributes:

            _key_:_attribute_=_value_...

          where =_value_ is omitted for Boolean attributes and no-_attribute_
          sets the attribute to false. Attribute values may appear in any order,
          but must be specified after any transform calls. The attributes are:

          *alias*=_ALIAS-NAME_::
          Sets _ALIAS-NAME_ as an alias for the projection key.

          *align*=_ALIGNMENT_::
          Specifies the output column data alignment. Used by the *table*
          format. The alignment values are:

          *left*:::
          Left (default).

          *center*:::
          Center.

          *right*:::
          Right.

          *label*=_LABEL_::
          A string value used to label output. Use :label="" or :label=''
          for no label. The *table* format uses _LABEL_ values as column
          headings. Also sets _LABEL_ as an alias for the projection key.
          The default label is the the disambiguated right hand parts of the
          column key name in ANGRY_SNAKE_CASE.

          [no-]*reverse*::
          Sets the key sort order to descending. *no-reverse* resets to the
          default ascending order.

          *sort*=_SORT-ORDER_::
          An integer counting from 1. Keys with lower sort-order are sorted
          first. Keys with same sort order are sorted left to right.

          *wrap*::
          Enables the column text to be wrapped if the table would otherwise
          be too wide for the display.
          """).format(
              description=resource_topics.ResourceDescription('projection'),
              transform_registry=
              resource_topics.TransformRegistryDescriptions()),

      'EXAMPLES': """\
          List a table of instance *zone* (sorted in descending order) and
          *name* (sorted by *name* and centered with column heading *INSTANCE*)
          and *creationTimestamp* (listed using the *strftime*(3) year-month-day
          format with column heading *START*):

            $ gcloud compute instances list --format='table(name:sort=2:align=center:label=INSTANCE, zone:sort=1:reverse, creationTimestamp.date("%Y-%m-%d"):label=START)'

          List only the *name*, *status* and *zone* instance resource keys in
          YAML format:

            $ gcloud compute instances list --format='yaml(name, status, zone)'

          List only the *config.account* key value(s) in the *info* resource:

            $ gcloud info --format='value(config.account)'
          """,
      }
