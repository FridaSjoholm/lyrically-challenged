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

"""Helper function to open a url using a proxy using httlib2 connections."""

import urllib2

from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import properties
import httplib2


class HttplibConnectionHandler(urllib2.HTTPHandler, urllib2.HTTPSHandler):
  """urllib2 Handler Class to use httplib2 connections.

  This handler makes urllib2 use httplib2.HTTPSConnectionWithTimeout. The
  httplib2 connections can handle both HTTP and SOCKS proxies, passed via the
  ProxyInfo object. It also has CA_CERTS files and validates SSL certificates.
  """

  def http_open(self, req):
    def build(host, **kwargs):
      proxy_info = http_proxy.GetHttpProxyInfo()
      if callable(proxy_info):
        proxy_info = proxy_info('http')
      return httplib2.HTTPConnectionWithTimeout(
          host,
          proxy_info=proxy_info,
          **kwargs)
    return self.do_open(build, req)

  def https_open(self, req):
    def build(host, **kwargs):
      proxy_info = http_proxy.GetHttpProxyInfo()
      if callable(proxy_info):
        proxy_info = proxy_info('https')
      ca_certs = properties.VALUES.core.custom_ca_certs_file.Get()
      return httplib2.HTTPSConnectionWithTimeout(
          host,
          proxy_info=proxy_info,
          ca_certs=ca_certs,
          **kwargs)
    return self.do_open(build, req)


def urlopen(req, data=None, timeout=60):
  """Helper function that mimics urllib2.urlopen, but adds proxy information."""

  # We need to pass urllib2.ProxyHandler({}) to disable the proxy handling in
  # urllib2 open. If we don't, then urllib will substitute the host with the
  # proxy address and the HttplibConnectionHandler won't get the original host.
  # (the default urllib2.HTTPSHandler needs this substitution trickery)
  # We do the proxy detection in http_proxy.GetHttpProxyInfo and pass it to
  # httplib2.HTTPSConnectionWithTimeout via proxy info object.
  # httplib2.HTTPSConnectionWithTimeout takes care of handling proxies.
  opener = urllib2.build_opener(urllib2.ProxyHandler({}),
                                HttplibConnectionHandler())
  return opener.open(req, data, timeout)
