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
"""Utilities for the cloudbuild API."""
from googlecloudsdk.core import apis


_API_NAME = 'cloudbuild'
_API_VERSION = 'v1'


def GetMessagesModule():
  return apis.GetMessagesModule(_API_NAME, _API_VERSION)


def GetClientClass():
  return apis.GetClientClass(_API_NAME, _API_VERSION)


def GetClientInstance(use_http=True):
  return apis.GetClientInstance(_API_NAME, _API_VERSION, no_http=(not use_http))
