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
"""Utilities for the API to configure cross-project networking (XPN)."""
from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.core import exceptions


_API_VERSION = 'alpha'


class XpnApiError(exceptions.Error):
  pass


class XpnClient(object):
  """A client for interacting with the cross-project networking (XPN) API.

  The XPN API is a subset of the Google Compute Engine API.
  """

  def __init__(self, compute_client):
    self.compute_client = compute_client
    self.client = compute_client.apitools_client
    self.messages = compute_client.messages

  # TODO(b/30465957): Refactor to use apitools clients directly and not the
  # compute utilities
  def _MakeRequest(self, request, errors):
    return self.compute_client.MakeRequests(
        requests=[request],
        errors_to_collect=errors)

  def _MakeRequestSync(self, request_tuple, operation_msg=None):
    errors = []
    results = list(self._MakeRequest(request_tuple, errors))

    if errors:
      operation_msg = operation_msg or 'complete all requests'
      msg = 'Could not {0}:'.format(operation_msg)
      utils.RaiseException(errors, XpnApiError, msg)

    return results[0]  # if there were no errors, this will exist

  def EnableHost(self, project):
    """Enable the project with the given ID as an XPN host."""
    request_tuple = (
        self.client.projects,
        'EnableXpnHost',
        self.messages.ComputeProjectsEnableXpnHostRequest(project=project))
    msg = 'enable [{project}] as XPN host'.format(project=project)
    self._MakeRequestSync(request_tuple, msg)

  def DisableHost(self, project):
    """Disable the project with the given ID as an XPN host."""
    request_tuple = (
        self.client.projects,
        'DisableXpnHost',
        self.messages.ComputeProjectsDisableXpnHostRequest(project=project))
    msg = 'disable [{project}] as XPN host'.format(project=project)
    self._MakeRequestSync(request_tuple, msg)

  def GetHostProject(self, project):
    """Get the XPN host for the given project."""
    request_tuple = (
        self.client.projects,
        'GetXpnHost',
        self.messages.ComputeProjectsGetXpnHostRequest(project=project))
    msg = 'get XPN host for project [{project}]'.format(project=project)
    return self._MakeRequestSync(request_tuple, msg)

  def ListEnabledResources(self, project):
    request_tuple = (
        self.client.projects,
        'GetXpnResources',
        self.messages.ComputeProjectsGetXpnResourcesRequest(project=project))
    msg = ('list resources that are enabled to use project [{project}] as an '
           'XPN host').format(project=project)
    return self._MakeRequestSync(request_tuple, msg)

  def ListOrganizationHostProjects(self, project, organization_id):
    """List the projects in an organization that are enabled as XPN hosts.

    Args:
      project: str, project ID to make the request with.
      organization_id: str, the ID of the organization to list XPN hosts
          for. If None, the organization is inferred from the project.

    Returns:
      Generator for `Project`s corresponding to XPN hosts in the organization.
    """
    request = self.messages.ComputeProjectsListXpnHostsRequest(
        project=project,
        projectsListXpnHostsRequest=self.messages.ProjectsListXpnHostsRequest(
            organization=organization_id))
    if organization_id:
      msg = ('list XPN hosts for organization [{0}] '
             '(current project is [{1}])').format(organization_id, project)
    else:
      msg = ('list XPN hosts for organization inferred from project [{0}]'
            ).format(project)
    # TODO(b/29896285): Use apitools list_pager.YieldFromList when API fully
    # supports paging
    items = self._MakeRequestSync(
        (self.client.projects, 'ListXpnHosts', request), msg).items
    # Return a generator, since that's what will happend when we use
    # YieldFromList
    return iter(items)

  def _EnableXpnAssociatedResource(self, host_project, associated_resource,
                                   xpn_resource_type):
    """Associate the given resource with the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_resource: ID of the resource to associate with host_project
      xpn_resource_type: XpnResourceId.TypeValueValuesEnum, the type of the
         resource
    """
    projects_enable_request = self.messages.ProjectsEnableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(
            id=associated_resource,
            type=xpn_resource_type)
    )
    request = self.messages.ComputeProjectsEnableXpnResourceRequest(
        project=host_project,
        projectsEnableXpnResourceRequest=projects_enable_request)
    request_tuple = (self.client.projects, 'EnableXpnResource', request)
    msg = ('enable resource [{0}] as an associated resource '
           'for project [{1}]').format(associated_resource, host_project)
    self._MakeRequestSync(request_tuple, msg)

  def EnableXpnAssociatedProject(self, host_project, associated_project):
    """Associate the given project with the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_project: ID of the project to associate
    """
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    self._EnableXpnAssociatedResource(
        host_project, associated_project, xpn_resource_type=xpn_types.PROJECT)

  def _DisableXpnAssociatedResource(self, host_project, associated_resource,
                                    xpn_resource_type):
    """Disassociate the given resource from the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_resource: ID of the resource to disassociate from host_project
      xpn_resource_type: XpnResourceId.TypeValueValuesEnum, the type of the
         resource
    """
    projects_disable_request = self.messages.ProjectsDisableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(
            id=associated_resource,
            type=xpn_resource_type)
    )
    request = self.messages.ComputeProjectsDisableXpnResourceRequest(
        project=host_project,
        projectsDisableXpnResourceRequest=projects_disable_request)
    request_tuple = (self.client.projects, 'DisableXpnResource', request)
    msg = ('disable resource [{0}] as an associated resource '
           'for project [{1}]').format(associated_resource, host_project)
    self._MakeRequestSync(request_tuple, msg)

  def DisableXpnAssociatedProject(self, host_project, associated_project):
    """Disassociate the given project from the given XPN host project.

    Args:
      host_project: str, ID of the XPN host project
      associated_project: ID of the project to disassociate from host_project
    """
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    self._DisableXpnAssociatedResource(
        host_project, associated_project, xpn_resource_type=xpn_types.PROJECT)


def GetXpnClient():
  return XpnClient(client_adapter.ClientAdapter(_API_VERSION))
