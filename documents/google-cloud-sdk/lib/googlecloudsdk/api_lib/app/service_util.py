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

"""Utilities for dealing with service resources."""

from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import text


class ServiceValidationError(exceptions.Error):
  pass


class ServicesDeleteError(exceptions.Error):
  pass


class ServicesNotFoundError(exceptions.Error):

  @classmethod
  def FromServiceLists(cls, requested_services, all_services):
    """Format a ServiceNotFoundError.

    Args:
      requested_services: list of str, IDs of services that were not found.
      all_services: list of str, IDs of all available services

    Returns:
      ServicesNotFoundError, error with properly formatted message
    """
    return cls(
        'The following {0} not found: [{1}]\n\n'
        'All services: [{2}]'.format(
            text.Pluralize(len(requested_services), 'service was',
                           plural='services were'),
            ', '.join(requested_services),
            ', '.join(all_services)))


class ServicesSplitTrafficError(exceptions.Error):
  pass


class Service(object):
  """Value class representing a service resource."""

  def __init__(self, project, id_, split=None):
    self.project = project
    self.id = id_
    self.split = split or {}

  def __eq__(self, other):
    return (type(other) is Service and
            self.project == other.project and self.id == other.id)

  def __ne__(self, other):
    return not self == other

  @classmethod
  def FromResourcePath(cls, path):
    parts = path.split('/')
    if len(parts) != 2:
      raise ServiceValidationError('[{0}] is not a valid resource path. '
                                   'Expected <project>/<service>.')
    return cls(*parts)

  # TODO(b/25662075): convert to use functools.total_ordering
  def __lt__(self, other):
    return (self.project, self.id) < (other.project, other.id)

  def __le__(self, other):
    return (self.project, self.id) <= (other.project, other.id)

  def __gt__(self, other):
    return (self.project, self.id) > (other.project, other.id)

  def __ge__(self, other):
    return (self.project, self.id) >= (other.project, other.id)

  def __repr__(self):
    return '{0}/{1}'.format(self.project, self.id)


def _ValidateServicesAreSubset(filtered_services, all_services):
  not_found_services = set(filtered_services) - set(all_services)
  if not_found_services:
    raise ServicesNotFoundError.FromServiceLists(not_found_services,
                                                 all_services)


def GetMatchingServices(all_services, args_services):
  """Return a list of services to act on based on user arguments.

  Args:
    all_services: list of Service representing all services in the project.
    args_services: list of string, service IDs to filter for.
      If empty, match all services.

  Returns:
    list of matching Service

  Raises:
    ServiceValidationError: If an improper combination of arguments is given
  """
  if not args_services:
    args_services = [s.id for s in all_services]
  _ValidateServicesAreSubset(args_services, [s.id for s in all_services])
  return [s for s in all_services if s.id in args_services]


def ParseTrafficAllocations(args_allocations, split_method):
  """Parses the user-supplied allocations into a format acceptable by the API.

  Args:
    args_allocations: The raw allocations passed on the command line. A dict
      mapping version_id (str) to the allocation (float).
    split_method: Whether the traffic will be split by ip or cookie. This
      affects the format we specify the splits in.

  Returns:
    A dict mapping version id (str) to traffic split (float).

  Raises:
    ServicesSplitTrafficError: if the sum of traffic allocations is zero.
  """
  # Splitting by IP allows 2 decimal places, splitting by cookie allows 3.
  max_decimal_places = 2 if split_method == 'ip' else 3
  sum_of_splits = sum([float(s) for s in args_allocations.values()])
  if sum_of_splits < 10 ** -max_decimal_places:
    raise ServicesSplitTrafficError(
        'Cannot set traffic split to zero. If you would like a version to '
        'receive no traffic, send 100% of traffic to other versions or delete '
        'the service.')

  allocations = {}
  for version, split in args_allocations.iteritems():
    allocation = float(split) / sum_of_splits
    allocation = round(allocation, max_decimal_places)
    allocations[version] = allocation

  # The API requires that these sum to 1.0. This is hard to get exactly correct,
  # (think .33, .33, .33) so we take our difference and subtract it from a
  # random element.
  total_splits = sum(allocations.values())
  difference = total_splits - 1.0

  allocations[sorted(allocations.keys())[0]] -= difference
  return allocations


def DeleteServices(api_client, services):
  """Delete the given services."""
  errors = {}
  for service in services:
    try:
      with progress_tracker.ProgressTracker(
          'Deleting [{0}]'.format(service.id)):
        api_client.DeleteService(service.id)
    except (calliope_exceptions.HttpException, operations_util.OperationError,
            operations_util.OperationTimeoutError) as err:
      errors[service.id] = str(err)

  if errors:
    printable_errors = {}
    for service_id, error_msg in errors.items():
      printable_errors[service_id] = '[{0}]: {1}'.format(service_id,
                                                         error_msg)
    raise ServicesDeleteError(
        'Issue deleting {0}: [{1}]\n\n'.format(
            text.Pluralize(len(printable_errors), 'service'),
            ', '.join(printable_errors.keys())) +
        '\n\n'.join(printable_errors.values()))

