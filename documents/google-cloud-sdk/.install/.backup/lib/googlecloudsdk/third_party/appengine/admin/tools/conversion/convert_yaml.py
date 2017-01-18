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
"""A script for converting between legacy YAML and public JSON representation.

Example invocation:
  convert_yaml.py app.yaml > app.json
"""

import argparse
import json
import sys

import yaml

from googlecloudsdk.third_party.appengine.admin.tools.conversion import yaml_schema_v1
from googlecloudsdk.third_party.appengine.admin.tools.conversion import yaml_schema_v1beta


API_VERSION_SCHEMAS = {
    'v1beta4': yaml_schema_v1beta,
    'v1beta5': yaml_schema_v1beta,
    'v1': yaml_schema_v1
}


def main():
  parser = argparse.ArgumentParser(description='Convert between legacy YAML '
                                   'and public JSON representations of App '
                                   'Engine versions')
  parser.add_argument('input_file')
  parser.add_argument('--api_version', dest='api_version', default='v1beta5',
                      choices=sorted(API_VERSION_SCHEMAS.keys()))

  args = parser.parse_args()

  with open(args.input_file) as input_file:
    input_yaml = yaml.safe_load(input_file)

  yaml_schema = API_VERSION_SCHEMAS[args.api_version]

  converted_yaml = yaml_schema.SCHEMA.ConvertValue(input_yaml)
  json.dump(converted_yaml, sys.stdout, indent=2, sort_keys=True)


if __name__ == '__main__':
  main()

