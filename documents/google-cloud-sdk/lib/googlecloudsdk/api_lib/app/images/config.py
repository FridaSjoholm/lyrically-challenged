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

"""Magic constants for images module."""

# The version of the docker API the docker-py client uses.
# Warning: other versions might have different return values for some functions.
DOCKER_PY_VERSION = 'auto'

# Timeout of HTTP request from docker-py client to docker daemon, in seconds.
DOCKER_D_REQUEST_TIMEOUT = 300

DOCKER_IMAGE_NAME_FORMAT = 'us.gcr.io/{display}/appengine/{service}.{version}'
DOCKER_IMAGE_TAG = 'latest'
DOCKER_IMAGE_NAME_DOMAIN_FORMAT = (
    'us.gcr.io/{domain}/{display}/appengine/{service}.{version}')

# Name of the a Dockerfile.
DOCKERFILE = 'Dockerfile'

# A map of runtimes values if they need to be overwritten to match our
# base Docker images naming rules.
CANONICAL_RUNTIMES = {'java7': 'java'}
