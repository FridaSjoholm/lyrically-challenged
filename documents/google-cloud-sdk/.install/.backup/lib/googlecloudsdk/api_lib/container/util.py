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

"""Common utilities for the containers tool."""
import os
import StringIO
import distutils.version as dist_version


from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms


HTTP_ERROR_FORMAT = (
    'ResponseError: code={status_code}, message={status_message}')


class Error(core_exceptions.Error):
  """Class for errors raised by container commands."""


def ConstructList(title, items):
  buf = StringIO.StringIO()
  resource_printer.Print(items, 'list[title="{0}"]'.format(title), out=buf)
  return buf.getvalue()


MISSING_KUBECTL_MSG = """\
Accessing a Container Engine cluster requires the kubernetes commandline
client [kubectl]. To install, run
  $ gcloud components install kubectl
"""

_KUBECTL_COMPONENT_NAME = 'kubectl'


def _KubectlInstalledAsComponent():
  if config.Paths().sdk_root is not None:
    platform = platforms.Platform.Current()
    manager = update_manager.UpdateManager(platform_filter=platform, warn=False)
    installed_components = manager.GetCurrentVersionsInformation()
    return _KUBECTL_COMPONENT_NAME in installed_components


def CheckKubectlInstalled():
  """Verify that the kubectl component is installed or print a warning."""
  if (not file_utils.FindExecutableOnPath(_KUBECTL_COMPONENT_NAME) and
      not _KubectlInstalledAsComponent()):
    log.warn(MISSING_KUBECTL_MSG)


KUBECONFIG_USAGE_FMT = '''\
kubeconfig entry generated for {cluster}.'''

MIN_GCP_AUTH_PROVIDER_VERSION = '1.3.0'


class MissingEndpointError(Error):
  """Error for attempting to persist a cluster that has no endpoint."""

  def __init__(self, cluster):
    super(MissingEndpointError, self).__init__(
        'cluster {0} is missing endpoint. Is it still PROVISIONING?'.format(
            cluster.name))


class ClusterConfig(object):
  """Encapsulates persistent cluster config data.

  Call ClusterConfig.Load() or ClusterConfig.Persist() to create this
  object.
  """

  _CONFIG_DIR_FORMAT = '{project}_{zone}_{cluster}'

  KUBECONTEXT_FORMAT = 'gke_{project}_{zone}_{cluster}'

  def __init__(self, **kwargs):
    self.cluster_name = kwargs['cluster_name']
    self.zone_id = kwargs['zone_id']
    self.project_id = kwargs['project_id']
    self.server = kwargs['server']
    # auth options are basic (user,password), bearer token, auth-provider, or
    # client certificate.
    self.username = kwargs.get('username')
    self.password = kwargs.get('password')
    self.token = kwargs.get('token')
    self.auth_provider = kwargs.get('auth_provider')
    self.ca_data = kwargs.get('ca_data')
    self.client_cert_data = kwargs.get('client_cert_data')
    self.client_key_data = kwargs.get('client_key_data')

  def __str__(self):
    return 'ClusterConfig{project:%s, cluster:%s, zone:%s, endpoint:%s}' % (
        self.project_id, self.cluster_name, self.zone_id, self.endpoint)

  def _Fullpath(self, filename):
    return os.path.abspath(os.path.join(self.config_dir, filename))

  @property
  def config_dir(self):
    return ClusterConfig.GetConfigDir(
        self.cluster_name, self.zone_id, self.project_id)

  @property
  def kube_context(self):
    return ClusterConfig.KubeContext(
        self.cluster_name, self.zone_id, self.project_id)

  @property
  def has_cert_data(self):
    return bool(self.client_key_data and self.client_cert_data)

  @property
  def has_certs(self):
    return self.has_cert_data

  @property
  def has_ca_cert(self):
    return self.ca_data

  @staticmethod
  def UseGCPAuthProvider(cluster):
    return (cluster.currentMasterVersion and
            dist_version.LooseVersion(cluster.currentMasterVersion) >=
            dist_version.LooseVersion(MIN_GCP_AUTH_PROVIDER_VERSION) and
            not properties.VALUES.container.use_client_certificate.GetBool())

  @staticmethod
  def GetConfigDir(cluster_name, zone_id, project_id):
    return os.path.join(
        config.Paths().container_config_path,
        ClusterConfig._CONFIG_DIR_FORMAT.format(
            project=project_id, zone=zone_id, cluster=cluster_name))

  @staticmethod
  def KubeContext(cluster_name, zone_id, project_id):
    return ClusterConfig.KUBECONTEXT_FORMAT.format(
        project=project_id, cluster=cluster_name, zone=zone_id)

  def GenKubeconfig(self):
    """Generate kubeconfig for this cluster."""
    context = self.kube_context
    kubeconfig = kconfig.Kubeconfig.Default()
    cluster_kwargs = {}
    user_kwargs = {
        'token': self.token,
        'username': self.username,
        'password': self.password,
        'auth_provider': self.auth_provider,
    }
    if self.has_ca_cert:
      cluster_kwargs['ca_data'] = self.ca_data
    if self.has_cert_data:
      user_kwargs['cert_data'] = self.client_cert_data
      user_kwargs['key_data'] = self.client_key_data

    # Use same key for context, cluster, and user
    kubeconfig.contexts[context] = kconfig.Context(context, context, context)
    kubeconfig.users[context] = kconfig.User(context, **user_kwargs)
    kubeconfig.clusters[context] = kconfig.Cluster(
        context, self.server, **cluster_kwargs)
    kubeconfig.SetCurrentContext(context)
    kubeconfig.SaveToFile()

    path = kconfig.Kubeconfig.DefaultPath()
    log.debug('Saved kubeconfig to %s', path)
    log.status.Print(KUBECONFIG_USAGE_FMT.format(
        cluster=self.cluster_name, context=context))

  @classmethod
  def Persist(cls, cluster, project_id):
    """Save config data for the given cluster.

    Persists config file and kubernetes auth file for the given cluster
    to cloud-sdk config directory and returns ClusterConfig object
    encapsulating the same data.

    Args:
      cluster: valid Cluster message to persist config data for.
      project_id: project that owns this cluster.
    Returns:
      ClusterConfig of the persisted data.
    Raises:
      Error: if cluster has no endpoint (will be the case for first few
        seconds while cluster is PROVISIONING).
    """
    if not cluster.endpoint:
      raise MissingEndpointError(cluster)
    kwargs = {
        'cluster_name': cluster.name,
        'zone_id': cluster.zone,
        'project_id': project_id,
        'server': 'https://' + cluster.endpoint,
    }
    auth = cluster.masterAuth
    if auth and auth.clusterCaCertificate:
      kwargs['ca_data'] = auth.clusterCaCertificate
    else:
      # This should not happen unless the cluster is in an unusual error
      # state.
      log.warn('Cluster is missing certificate authority data.')

    if cls.UseGCPAuthProvider(cluster):
      kwargs['auth_provider'] = 'gcp'
    else:
      if auth.clientCertificate and auth.clientKey:
        kwargs['client_key_data'] = auth.clientKey
        kwargs['client_cert_data'] = auth.clientCertificate
      # TODO(user): these are not needed if cluster has certs, though they
      # are useful for testing, e.g. with curl. Consider removing if/when the
      # apiserver no longer supports insecure (no certs) requests.
      # TODO(user): use api_adapter instead of getattr, or remove bearerToken
      # support
      if getattr(auth, 'bearerToken', None):
        kwargs['token'] = auth.bearerToken
      else:
        username = getattr(auth, 'user', None) or getattr(auth, 'username',
                                                          None)
        kwargs['username'] = username
        kwargs['password'] = auth.password

    c_config = cls(**kwargs)
    c_config.GenKubeconfig()
    return c_config

  @classmethod
  def Load(cls, cluster_name, zone_id, project_id):
    """Load and verify config for given cluster.

    Args:
      cluster_name: name of cluster to load config for.
      zone_id: compute zone the cluster is running in.
      project_id: project in which the cluster is running.
    Returns:
      ClusterConfig for the cluster, or None if config data is missing or
      incomplete.
    """
    log.debug('Loading cluster config for cluster=%s, zone=%s project=%s',
              cluster_name, zone_id, project_id)
    k = kconfig.Kubeconfig.Default()

    key = cls.KubeContext(cluster_name, zone_id, project_id)

    cluster = k.clusters.get(key) and k.clusters[key].get('cluster')
    user = k.users.get(key) and k.users[key].get('user')
    context = k.contexts.get(key) and k.contexts[key].get('context')
    if not cluster or not user or not context:
      log.debug('missing kubeconfig entries for %s', key)
      return None
    if context.get('user') != key or context.get('cluster') != key:
      log.debug('invalid context %s', context)
      return None

    # Verify cluster data
    server = cluster.get('server')
    insecure = cluster.get('insecure-skip-tls-verify')
    ca_data = cluster.get('certificate-authority-data')
    if not server:
      log.debug('missing cluster.server entry for %s', key)
      return None
    if insecure:
      if ca_data:
        log.debug('cluster cannot specify both certificate-authority-data '
                  'and insecure-skip-tls-verify')
        return None
    elif not ca_data:
      log.debug('cluster must specify one of certificate-authority-data|'
                'insecure-skip-tls-verify')
      return None

    # Verify user data
    username = user.get('username')
    password = user.get('password')
    token = user.get('token')
    auth_provider = user.get('auth-provider')
    cert_data = user.get('client-certificate-data')
    key_data = user.get('client-key-data')
    cert_auth = cert_data and key_data
    basic_auth = username and password
    has_valid_auth = auth_provider or cert_auth or token or basic_auth
    if not has_valid_auth:
      log.debug('missing auth info for user %s: %s', key, user)
      return None
    # Construct ClusterConfig
    kwargs = {
        'cluster_name': cluster_name,
        'zone_id': zone_id,
        'project_id': project_id,
        'server': server,
        'username': username,
        'password': password,
        'token': token,
        'auth_provider': auth_provider,
        'ca_data': ca_data,
        'client_key_data': key_data,
        'client_cert_data': cert_data,
    }
    return cls(**kwargs)

  @classmethod
  def Purge(cls, cluster_name, zone_id, project_id):
    config_dir = cls.GetConfigDir(cluster_name, zone_id, project_id)
    if os.path.exists(config_dir):
      file_utils.RmTree(config_dir)
    # purge from kubeconfig
    kubeconfig = kconfig.Kubeconfig.Default()
    kubeconfig.Clear(cls.KubeContext(cluster_name, zone_id, project_id))
    kubeconfig.SaveToFile()
    log.debug('Purged cluster config from %s', config_dir)
