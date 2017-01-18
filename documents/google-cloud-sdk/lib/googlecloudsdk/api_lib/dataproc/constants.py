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
"""Constants for the dataproc tool."""

# TODO(user): Move defaults to the server
from googlecloudsdk.core import apis as core_apis

messages = core_apis.GetMessagesModule('dataproc', 'v1')
# Job Status states that do not change.
TERMINAL_JOB_STATES = [
    messages.JobStatus.StateValueValuesEnum.CANCELLED,
    messages.JobStatus.StateValueValuesEnum.DONE,
    messages.JobStatus.StateValueValuesEnum.ERROR,
]

# Path inside of GCS bucket, where Dataproc stores metadata.
GCS_METADATA_PREFIX = 'google-cloud-dataproc-metainfo'

# Beginning of driver output files.
JOB_OUTPUT_PREFIX = 'driveroutput'

# The scopes that will be added to user-specified scopes. Used for
# documentation only. Keep in sync with server specified list.
MINIMUM_SCOPE_URIS = [
    'https://www.googleapis.com/auth/cloud.useraccounts.readonly',
    'https://www.googleapis.com/auth/devstorage.read_write',
    'https://www.googleapis.com/auth/logging.write',
]

# The scopes that will be specified by default. Used fo documentation only.
# Keep in sync with server specified list.
ADDITIONAL_DEFAULT_SCOPE_URIS = [
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/bigtable.admin.table',
    'https://www.googleapis.com/auth/bigtable.data',
    'https://www.googleapis.com/auth/devstorage.full_control',
]

# The default page size for list pagination.
DEFAULT_PAGE_SIZE = 100
