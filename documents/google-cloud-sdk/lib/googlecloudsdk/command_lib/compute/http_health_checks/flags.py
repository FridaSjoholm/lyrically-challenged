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

"""Flags and helpers for the compute http-health-checks commands."""

from googlecloudsdk.command_lib.compute import flags as compute_flags


def HttpHealthCheckArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='http health check',
      completion_resource_id='compute.httpHealthChecks',
      plural=False,
      required=required,
      global_collection='compute.httpHealthChecks',
      short_help='The name of the HTTP health check.')


def HttpHealthCheckArgumentForTargetPool(action, required=True):
  return compute_flags.ResourceArgument(
      resource_name='http health check',
      name='--http-health-check',
      completion_resource_id='compute.httpHealthChecks',
      plural=False,
      required=required,
      global_collection='compute.httpHealthChecks',
      short_help=('Specifies an HTTP health check object to {0} the '
                  'target pool.'.format(action)))


def HttpHealthCheckArgumentForTargetPoolCreate(required=True):
  return compute_flags.ResourceArgument(
      resource_name='http health check',
      name='--http-health-check',
      completion_resource_id='compute.httpHealthChecks',
      plural=False,
      required=required,
      global_collection='compute.httpHealthChecks',
      short_help=(
          'Specifies HttpHealthCheck to determine the health of instances '
          'in the pool.'),
      detailed_help="""\
        Specifies an HTTP health check resource to use to determine the health
        of instances in this pool. If no health check is specified, traffic will
        be sent to all instances in this target pool as if the instances
        were healthy, but the health status of this pool will appear as
        unhealthy as a warning that this target pool does not have a health
        check.
        """)
