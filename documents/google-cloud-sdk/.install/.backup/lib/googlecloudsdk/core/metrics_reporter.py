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

"""Script for reporting gcloud metrics."""

import os
import pickle
import sys

from googlecloudsdk.core import http_proxy

try:
  # pylint:disable=g-import-not-at-top
  import httplib2
except ImportError:
  # Do nothing if we can't import the lib.
  sys.exit(0)

# If outgoing packets are getting dropped, httplib2 will hang forever waiting
# for a response.
TIMEOUT_IN_SEC = 10


def ReportMetrics(metrics_file_path):
  """Sends the specified anonymous usage event to the given analytics endpoint.

  Args:
      metrics_file_path: str, File with pickled metrics (list of tuples).
  """
  with open(metrics_file_path, 'rb') as metrics_file:
    metrics = pickle.load(metrics_file)
  os.remove(metrics_file_path)

  http = httplib2.Http(timeout=TIMEOUT_IN_SEC,
                       proxy_info=http_proxy.GetHttpProxyInfo())

  for metric in metrics:
    headers = {'user-agent': metric[3]}
    http.request(metric[0], method=metric[1], body=metric[2], headers=headers)

if __name__ == '__main__':
  try:
    ReportMetrics(sys.argv[1])
  # pylint: disable=bare-except, Never fail or output a stacktrace here.
  except:
    pass
