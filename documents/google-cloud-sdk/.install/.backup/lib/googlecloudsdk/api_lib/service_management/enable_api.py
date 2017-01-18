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

"""service-management enable helper functions."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.core import log


def EnableServiceApiCall(project_id, service_name):
  """Make API call to enable a specific API.

  Args:
    project_id: The ID of the project for which to enable the service.
    service_name: The name of the service to enable on the project.

  Returns:
    The result of the Enable operation
  """

  client = services_util.GetClientInstance()
  messages = services_util.GetMessagesModule()

  request = messages.ServicemanagementServicesEnableRequest(
      serviceName=service_name,
      enableServiceRequest=messages.EnableServiceRequest(
          consumerId='project:' + project_id
      )
  )
  return client.services.Enable(request)


def EnableServiceIfDisabled(project_id, service_name, async=False):
  """Check to see if the service is enabled, and if it is not, do so.

  Args:
    project_id: The ID of the project for which to enable the service.
    service_name: The name of the service to enable on the project.
    async: bool, if True, return the operation ID immediately, without waiting
           for the op to complete.
  """

  client = services_util.GetClientInstance()

  # Get the list of enabled services.
  request = services_util.GetEnabledListRequest(project_id)
  services = list_pager.YieldFromList(
      client.services,
      request,
      batch_size_attribute='pageSize',
      field='services')

  # If the service is already present in the list of enabled services, return
  # early, otherwise, enable the service.
  for service in services:
    if service.serviceName.lower() == service_name.lower():
      log.debug('Service [{0}] is already enabled for project [{1}]'.format(
          service_name, project_id))
      return

  # If the service is not yet enabled, enable it
  log.status.Print('Enabling service {0} on project {1}...'.format(
      service_name, project_id))

  # Enable the service
  operation = EnableServiceApiCall(project_id, service_name)

  # Process the enable operation
  services_util.ProcessOperationResult(operation, async)
