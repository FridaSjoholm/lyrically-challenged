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
#
"""Contains utilities for holding and formatting install information.

This is useful for the output of 'gcloud info', which in turn is extremely
useful for debugging issues related to weird installations, out-of-date
installations, and so on.
"""

import datetime
import os
import re
import StringIO
import sys
import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.diagnostics import http_proxy_setup
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import http_proxy_types
from googlecloudsdk.core.util import platforms


class InfoHolder(object):
  """Base object to hold all the configuration info."""

  def __init__(self):
    self.basic = BasicInfo()
    self.installation = InstallationInfo()
    self.config = ConfigInfo()
    self.env_proxy = ProxyInfoFromEnvironmentVars()
    self.logs = LogsInfo()

  def __str__(self):
    out = StringIO.StringIO()
    out.write(unicode(self.basic) + '\n')
    out.write(unicode(self.installation) + '\n')
    out.write(unicode(self.config) + '\n')
    if unicode(self.env_proxy):
      out.write(unicode(self.env_proxy) + '\n')
    out.write(unicode(self.logs) + '\n')
    return out.getvalue()


class BasicInfo(object):
  """Holds basic information about your system setup."""

  def __init__(self):
    platform = platforms.Platform.Current()
    self.version = config.CLOUD_SDK_VERSION
    self.operating_system = platform.operating_system
    self.architecture = platform.architecture
    self.python_version = sys.version
    self.site_packages = 'site' in sys.modules

  def __str__(self):
    return textwrap.dedent(u"""\
        Google Cloud SDK [{version}]

        Platform: [{os}, {arch}]
        Python Version: [{python_version}]
        Python Location: [{python_location}]
        Site Packages: [{site_packages}]
        """.format(
            version=self.version,
            os=self.operating_system.name,
            arch=self.architecture.name,
            python_location=sys.executable,
            python_version=self.python_version.replace('\n', ' '),
            site_packages='Enabled' if self.site_packages else 'Disabled'))


class InstallationInfo(object):
  """Holds information about your Cloud SDK installation."""

  def __init__(self):
    self.sdk_root = config.Paths().sdk_root
    self.release_channel = config.INSTALLATION_CONFIG.release_channel
    self.repo_url = config.INSTALLATION_CONFIG.snapshot_url
    repos = properties.VALUES.component_manager.additional_repositories.Get(
        validate=False)
    self.additional_repos = repos.split(',') if repos else []
    self.path = console_attr.GetEncodedValue(os.environ, 'PATH', '')

    if self.sdk_root:
      manager = update_manager.UpdateManager()
      self.components = manager.GetCurrentVersionsInformation()
      self.old_tool_paths = manager.FindAllOldToolsOnPath()
      paths = [os.path.realpath(p) for p in self.path.split(os.pathsep)]
      this_path = os.path.realpath(
          os.path.join(self.sdk_root,
                       update_manager.UpdateManager.BIN_DIR_NAME))
      # TODO(user): Validate symlinks in /usr/local/bin when we start
      # creating them.
      self.on_path = this_path in paths
    else:
      self.components = {}
      self.old_tool_paths = []
      self.on_path = False

    self.kubectl = file_utils.SearchForExecutableOnPath('kubectl')
    if self.kubectl:
      self.kubectl = self.kubectl[0]

  def __str__(self):
    out = StringIO.StringIO()
    out.write(u'Installation Root: [{0}]\n'.format(
        self.sdk_root if self.sdk_root else 'N/A'))
    if config.INSTALLATION_CONFIG.IsAlternateReleaseChannel():
      out.write(u'Release Channel: [{0}]\n'.format(self.release_channel))
      out.write(u'Repository URL: [{0}]\n'.format(self.repo_url))
    if self.additional_repos:
      out.write(u'Additional Repositories:\n  {0}\n'.format(
          '\n  '.join(self.additional_repos)))

    if self.components:
      components = [u'{0}: [{1}]'.format(name, value) for name, value in
                    self.components.iteritems()]
      out.write(u'Installed Components:\n  {0}\n'.format(
          u'\n  '.join(components)))

    out.write(u'System PATH: [{0}]\n'.format(self.path))
    out.write(u'Cloud SDK on PATH: [{0}]\n'.format(self.on_path))
    out.write(u'Kubectl on PATH: [{0}]\n'.format(self.kubectl or False))

    if self.old_tool_paths:
      out.write(u'\nWARNING: There are old versions of the Google Cloud '
                u'Platform tools on your system PATH.\n  {0}\n'
                .format('\n  '.join(self.old_tool_paths)))
    return out.getvalue()


class ConfigInfo(object):
  """Holds information about where config is stored and what values are set."""

  def __init__(self):
    cfg_paths = config.Paths()
    active_config = named_configs.ConfigurationStore.ActiveConfig()
    self.active_config_name = active_config.name
    self.paths = {
        'installation_properties_path': cfg_paths.installation_properties_path,
        'global_config_dir': cfg_paths.global_config_dir,
        'active_config_path': active_config.file_path
    }
    self.account = properties.VALUES.core.account.Get(validate=False)
    self.project = properties.VALUES.core.project.Get(validate=False)
    self.properties = properties.VALUES.AllValues()

  def __str__(self):
    out = StringIO.StringIO()
    out.write(u'Installation Properties: [{0}]\n'
              .format(self.paths['installation_properties_path']))
    out.write(u'User Config Directory: [{0}]\n'
              .format(self.paths['global_config_dir']))
    out.write(u'Active Configuration Name: [{0}]\n'
              .format(self.active_config_name))
    out.write(u'Active Configuration Path: [{0}]\n\n'
              .format(self.paths['active_config_path']))

    out.write(u'Account: [{0}]\n'.format(self.account))
    out.write(u'Project: [{0}]\n\n'.format(self.project))

    out.write(u'Current Properties:\n')
    for section, props in self.properties.iteritems():
      out.write(u'  [{section}]\n'.format(section=section))
      for name, value in props.iteritems():
        out.write(u'    {name}: [{value}]\n'.format(
            name=name, value=value))

    return out.getvalue()


class ProxyInfoFromEnvironmentVars(object):
  """Proxy info if it is in the environment but not set in gcloud properties."""

  def __init__(self):
    self.type = None
    self.address = None
    self.port = None
    self.username = None
    self.password = None

    try:
      proxy_info, from_gcloud = http_proxy_setup.EffectiveProxyInfo()
    except properties.InvalidValueError:
      return

    if proxy_info and not from_gcloud:
      self.type = http_proxy_types.REVERSE_PROXY_TYPE_MAP.get(
          proxy_info.proxy_type, 'UNKNOWN PROXY TYPE')
      self.address = proxy_info.proxy_host
      self.port = proxy_info.proxy_port
      self.username = proxy_info.proxy_user
      self.password = proxy_info.proxy_pass

  def __str__(self):
    if not any([self.type, self.address, self.port, self.username,
                self.password]):
      return ''

    out = StringIO.StringIO()
    out.write('Environmental Proxy Settings:\n')
    if self.type:
      out.write(u'  type: [{0}]\n'.format(self.type))
    if self.address:
      out.write(u'  address: [{0}]\n'.format(self.address))
    if self.port:
      out.write(u'  port: [{0}]\n'.format(self.port))
    if self.username:
      out.write(u'  username: [{0}]\n'.format(self.username))
    if self.password:
      out.write(u'  password: [{0}]\n'.format(self.password))
    return out.getvalue()


def RecentLogFiles(logs_dir, num=1):
  """Finds the most recent (not current) gcloud log files.

  Args:
    logs_dir: str, The path to the logs directory being used.
    num: the number of log files to find

  Returns:
    A list of full paths to the latest num log files, excluding the current
    log file. If there are fewer than num log files, include all of
    them. They will be in chronological order.
  """
  date_dirs = FilesSortedByName(logs_dir)
  if not date_dirs:
    return []

  found_files = []
  for date_dir in reversed(date_dirs):
    log_files = reversed(FilesSortedByName(date_dir) or [])
    found_files.extend(log_files)
    if len(found_files) >= num + 1:
      return found_files[1:num+1]

  return found_files[1:]


def LastLogFile(logs_dir):
  """Finds the last (not current) gcloud log file.

  Args:
    logs_dir: str, The path to the logs directory being used.

  Returns:
    str, The full path to the last (but not the currently in use) log file
    if it exists, or None.
  """
  files = RecentLogFiles(logs_dir)
  if files:
    return files[0]
  return None


def FilesSortedByName(directory):
  """Gets the list of files in the given directory, sorted by name.

  Args:
    directory: str, The path to the directory to list.

  Returns:
    [str], The full paths of the files, sorted by file name, or None.
  """
  if not os.path.isdir(directory):
    return None
  dates = os.listdir(directory)
  if not dates:
    return None
  return [os.path.join(directory, date) for date in sorted(dates)]


class LogData(object):
  """Representation of a log file.

  Stores information such as the name of the log file, its contents, and the
  command run.
  """

  # This precedes the traceback in the log file.
  TRACEBACK_MARKER = 'BEGIN CRASH STACKTRACE\n'

  # This shows the command run in the log file
  COMMAND_REGEXP = r'Running (gcloud(?:\.[a-z-]+)*)'

  def __init__(self, filename, command, contents, traceback):
    self.filename = filename
    self.command = command
    self.contents = contents
    self.traceback = traceback

  def __str__(self):
    crash_detected = ' (crash detected)' if self.traceback else ''
    return u'[{0}]: [{1}]{2}'.format(self.relative_path, self.command,
                                     crash_detected)

  @property
  def relative_path(self):
    """Returns path of log file relative to log directory, or the full path.

    Returns the full path when the log file is not *in* the log directory.

    Returns:
      str, the relative or full path of log file.
    """
    logs_dir = config.Paths().logs_dir
    if logs_dir is None:
      return self.filename

    rel_path = os.path.relpath(self.filename, config.Paths().logs_dir)
    if rel_path.startswith(os.path.pardir + os.path.sep):
      # That is, filename is NOT in logs_dir
      return self.filename

    return rel_path

  @property
  def date(self):
    """Return the date that this log file was created, based on its filename.

    Returns:
      datetime.datetime that the log file was created or None, if the filename
        pattern was not recognized.
    """
    datetime_string = ':'.join(os.path.split(self.relative_path))
    datetime_format = (log.DAY_DIR_FORMAT + ':' + log.FILENAME_FORMAT +
                       log.LOG_FILE_EXTENSION)
    try:
      return datetime.datetime.strptime(datetime_string, datetime_format)
    except ValueError:
      # This shouldn't happen, but it's better not to crash because of it.
      return None

  @classmethod
  def FromFile(cls, log_file):
    """Parse the file at the given path into a LogData.

    Args:
      log_file: str, the path to the log file to read

    Returns:
      LogData, representation of the log file
    """
    with open(log_file) as log_fp:
      contents = log_fp.read()
      traceback = None
      command = None
      match = re.search(cls.COMMAND_REGEXP, contents)
      if match:
        # ex. gcloud.group.subgroup.command
        dotted_cmd_string, = match.groups()
        command = ' '.join(dotted_cmd_string.split('.'))
      if cls.TRACEBACK_MARKER in contents:
        traceback = (contents.split(cls.TRACEBACK_MARKER)[-1])
        # Trim any log lines that follow the traceback
        traceback = re.split(log.LOG_PREFIX_PATTERN, traceback)[0]
        traceback = traceback.strip()
      return cls(log_file, command, contents, traceback)


class LogsInfo(object):
  """Holds information about where logs are located."""

  NUM_RECENT_LOG_FILES = 5

  def __init__(self):
    paths = config.Paths()
    self.logs_dir = paths.logs_dir
    self.last_log = LastLogFile(self.logs_dir)
    self.last_logs = RecentLogFiles(self.logs_dir, self.NUM_RECENT_LOG_FILES)

  def __str__(self):
    return textwrap.dedent(u"""\
        Logs Directory: [{logs_dir}]
        Last Log File: [{log_file}]
        """.format(logs_dir=self.logs_dir, log_file=self.last_log))

  def LastLogContents(self):
    if not self.last_log:
      return ''
    with open(self.last_log) as fp:
      return fp.read()

  def GetRecentRuns(self):
    """Return the most recent runs, as reported by info_holder.LogsInfo.

    Returns:
      A list of LogData
    """
    return [LogData.FromFile(log_file) for log_file in self.last_logs]
