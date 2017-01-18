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
"""Command for updating target SSL proxies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificate_flags)
from googlecloudsdk.command_lib.compute.target_ssl_proxies import flags


class Update(base.SilentCommand):
  """Update a target SSL proxy."""

  BACKEND_SERVICE_ARG = None
  SSL_CERTIFICATE_ARG = None
  TARGET_SSL_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    target_proxies_utils.AddProxyHeaderRelatedUpdateArgs(parser)

    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForTargetSslProxy(
            required=False))
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.SSL_CERTIFICATE_ARG = (
        ssl_certificate_flags.SslCertificateArgumentForOtherResource(
            'target SSL proxy', required=False))
    cls.SSL_CERTIFICATE_ARG.AddArgument(parser)
    cls.TARGET_SSL_PROXY_ARG = flags.TargetSslProxyArgument()
    cls.TARGET_SSL_PROXY_ARG.AddArgument(parser)

  def Run(self, args):
    if not (args.ssl_certificate or args.proxy_header or args.backend_service):
      raise exceptions.ToolException(
          'You must specify at least one of [--ssl-certificate], '
          '[--backend-service] or [--proxy-header].')

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    requests = []
    target_ssl_proxy_ref = self.TARGET_SSL_PROXY_ARG.ResolveAsResource(
        args, holder.resources)

    client = holder.client.apitools_client
    messages = holder.client.messages

    if args.ssl_certificate:
      ssl_certificate_ref = self.SSL_CERTIFICATE_ARG.ResolveAsResource(
          args, holder.resources)
      requests.append(
          (client.targetSslProxies,
           'SetSslCertificates',
           messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
               project=target_ssl_proxy_ref.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetSslCertificatesRequest=(
                   messages.TargetSslProxiesSetSslCertificatesRequest(
                       sslCertificates=[ssl_certificate_ref.SelfLink()])))))

    if args.backend_service:
      backend_service_ref = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, holder.resources)
      requests.append(
          (client.targetSslProxies,
           'SetBackendService',
           messages.ComputeTargetSslProxiesSetBackendServiceRequest(
               project=target_ssl_proxy_ref.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetBackendServiceRequest=(
                   messages.TargetSslProxiesSetBackendServiceRequest(
                       service=backend_service_ref.SelfLink())))))

    if args.proxy_header:
      proxy_header = (messages.TargetSslProxiesSetProxyHeaderRequest.
                      ProxyHeaderValueValuesEnum(args.proxy_header))
      requests.append(
          (client.targetSslProxies,
           'SetProxyHeader',
           messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
               project=target_ssl_proxy_ref.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetProxyHeaderRequest=(
                   messages.TargetSslProxiesSetProxyHeaderRequest(
                       proxyHeader=proxy_header)))))

    errors = []
    resources = holder.client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources


Update.detailed_help = {
    'brief': 'Update a target SSL proxy',
    'DESCRIPTION': """\

        *{command}* is used to change the SSL certificate, backend
        service or proxy header of existing target SSL proxies. A
        target SSL proxy is referenced by one or more forwarding rules
        which define which packets the proxy is responsible for
        routing. The target SSL proxy in turn points to a backend
        service which will handle the requests. The target SSL proxy
        also points to an SSL certificate used for server-side
        authentication.  """,
}
