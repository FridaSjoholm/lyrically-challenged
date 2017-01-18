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

"""Utilities for gcloud help text differences."""

import os
import re
import shutil

from googlecloudsdk.calliope import walker_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import text


# Help documents must not contain any of these invalid brand abbreviations.
INVALID_BRAND_ABBREVIATIONS = ['GAE', 'GCE', 'GCP', 'GCS', 'GKE']
# Max number of test changes to display.
TEST_CHANGES_DISPLAY_MAX = 32


class HelpTextUpdateError(exceptions.Error):
  """Update errors."""


def Whitelisted(path):
  """Checks if path is to be ignored in the directory differences.

  Args:
    path: A relative file path name to be checked.

  Returns:
    True if path is to be ignored in the directory differences.
  """
  return os.path.basename(path) == 'OWNERS'


def GetDirFilesRecursive(directory):
  """Generates the set of all files in directory and its children recursively.

  Args:
    directory: The directory path name.

  Returns:
    A set of all files in directory and its children recursively.
  """
  dirfiles = set()
  for dirpath, _, files in os.walk(directory):
    for name in files:
      dirfiles.add(os.path.normpath(os.path.join(dirpath, name)))
  return dirfiles


class DiffAccumulator(object):
  """A module for accumulating DirDiff() differences."""

  def __init__(self):
    self._changes = 0

  # pylint: disable=unused-argument
  def Ignore(self, relative_file):
    """Checks if relative_file should be ignored by DirDiff().

    Args:
      relative_file: A relative file path name to be checked.

    Returns:
      True if path is to be ignored in the directory differences.
    """
    return False

  # pylint: disable=unused-argument
  def AddChange(self, op, relative_file):
    """Called for each file difference.

    AddChange() can construct the {'add', 'delete', 'edit'} file operations that
    convert old_dir to match new_dir. Directory differences are ignored.

    This base implementation counts the number of changes.

    Args:
      op: The change operation string;
        'add'; relative_file is not in old_dir.
        'delete'; relative_file is not in new_dir.
        'edit'; relative_file is different in new_dir.
      relative_file: The old_dir and new_dir relative path name of a file that
        changed.

    Returns:
      A prune value. If non-zero then DirDiff() returns immediately with that
      value.
    """
    self._changes += 1
    return None

  def GetChanges(self):
    """Returns the accumulated changes."""
    return self._changes

  def Validate(self, relative_file, contents):
    """Called for each file for content validation.

    Args:
      relative_file: The old_dir and new_dir relative path name of an existing
        file.
      contents: The file contents string.
    """
    pass


def DirDiff(old_dir, new_dir, diff):
  """Calls diff.AddChange(op, file) on files that changed from old_dir new_dir.

  diff.AddChange() can construct the {'add', 'delete', 'edit'} file operations
  that convert old_dir to match new_dir. Directory differences are ignored.

  Args:
    old_dir: The old directory path name.
    new_dir: The new directory path name.
    diff: A DiffAccumulator instance.

  Returns:
    The return value of the first diff.AddChange() call that returns non-zero
    or None if all diff.AddChange() calls returned zero.
  """
  new_files = GetDirFilesRecursive(new_dir)
  old_files = GetDirFilesRecursive(old_dir)
  for new_file in new_files:
    relative_file = os.path.relpath(new_file, new_dir)
    if diff.Ignore(relative_file):
      continue
    with open(new_file, 'r') as f:
      new_contents = f.read()
    diff.Validate(relative_file, new_contents)
    old_file = os.path.normpath(os.path.join(old_dir, relative_file))
    if old_file in old_files:
      with open(old_file, 'r') as f:
        if f.read() == new_contents:
          continue
      op = 'edit'
    else:
      op = 'add'
    prune = diff.AddChange(op, relative_file)
    if prune:
      return prune
  for old_file in old_files:
    relative_file = os.path.relpath(old_file, old_dir)
    if diff.Ignore(relative_file):
      continue
    new_file = os.path.normpath(os.path.join(new_dir, relative_file))
    if new_file not in new_files:
      prune = diff.AddChange('delete', relative_file)
      if prune:
        return prune
  return None


class HelpTextAccumulator(DiffAccumulator):
  """Accumulates help text directory differences.

  Attributes:
    _changes: The list of DirDiff() (op, path) difference tuples.
    _invalid_file_count: The number of files that have invalid content.
  """

  def __init__(self):
    super(HelpTextAccumulator, self).__init__()
    self._changes = []
    self._invalid_abbreviations = re.compile(
        r'\b({0})\b'.format('|'.join(INVALID_BRAND_ABBREVIATIONS)))
    self._invalid_file_count = 0

  @property
  def invalid_file_count(self):
    return self._invalid_file_count

  def Ignore(self, relative_file):
    """Checks if relative_file should be ignored by DirDiff().

    Args:
      relative_file: A relative file path name to be checked.

    Returns:
      True if path is to be ignored in the directory differences.
    """
    return Whitelisted(relative_file)

  def Validate(self, relative_file, contents):
    if self._invalid_abbreviations.search(contents):
      log.error('[{0}] Help text cannot contain any of these abbreviations: '
                '[{1}].'.format(relative_file,
                                ','.join(INVALID_BRAND_ABBREVIATIONS)))
      self._invalid_file_count += 1

  def AddChange(self, op, relative_file):
    """Adds an DirDiff() difference tuple to the list of changes.

    Args:
      op: The difference operation, one of {'add', 'delete', 'edit'}.
      relative_file: The relative path of a file that has changed.

    Returns:
      None which signals DirDiff() to continue.
    """
    self._changes.append((op, relative_file))
    return None


class HelpTextUpdater(object):
  """Updates the help text directory to match the current CLI.

  Attributes:
    _cli: The Current CLI.
    _help_dir: The help text directory.
    _test: Show but do not apply operations if True.
  """

  def __init__(self, cli, directory, test=False):
    """Constructor.

    Args:
      cli: The Current CLI.
      directory: The help text directory.
      test: Show but do not apply operations if True.

    Raises:
      HelpTextUpdateError: If the destination directory does not exist.
    """
    if not os.path.isabs(directory):
      raise HelpTextUpdateError(
          'Destination directory [%s] must be absolute.' % directory)
    self._cli = cli
    self._help_dir = directory
    self._test = test

  def _Update(self):
    """Update() helper method. Returns the number of changed help text files."""
    with file_utils.TemporaryDirectory() as temp_dir:
      walker_util.HelpTextGenerator(self._cli, temp_dir).Walk(hidden=True)
      diff = HelpTextAccumulator()
      DirDiff(self._help_dir, temp_dir, diff)
      if diff.invalid_file_count:
        # Bail out early on invalid content errors. These must be corrected
        # before proceeding.
        raise HelpTextUpdateError(
            '{0} help text {1} with invalid content must be fixed.'.format(
                diff.invalid_file_count,
                text.Pluralize(diff.invalid_file_count, 'file')))

      ops = {}
      for op in ['add', 'delete', 'edit']:
        ops[op] = []

      changes = 0
      for op, path in sorted(diff.GetChanges()):
        changes += 1
        if not self._test or changes < TEST_CHANGES_DISPLAY_MAX:
          log.status.Print('{0} {1}'.format(op, path))
        ops[op].append(path)

      if self._test:
        if changes:
          if changes >= TEST_CHANGES_DISPLAY_MAX:
            log.status.Print('...')
          log.status.Print('{0} help test {1} changed'.format(
              changes, text.Pluralize(changes, 'file')))
        return changes

      op = 'add'
      if ops[op]:
        for path in ops[op]:
          dest_path = os.path.join(self._help_dir, path)
          subdir = os.path.dirname(dest_path)
          if subdir:
            file_utils.MakeDir(subdir)
          temp_path = os.path.join(temp_dir, path)
          shutil.copyfile(temp_path, dest_path)

      op = 'edit'
      if ops[op]:
        for path in ops[op]:
          dest_path = os.path.join(self._help_dir, path)
          temp_path = os.path.join(temp_dir, path)
          shutil.copyfile(temp_path, dest_path)

      op = 'delete'
      if ops[op]:
        for path in ops[op]:
          dest_path = os.path.join(self._help_dir, path)
          try:
            os.remove(dest_path)
          except OSError:
            pass

      return changes

  def Update(self):
    """Updates the help text directory to match the current CLI.

    Raises:
      HelpTextUpdateError: If the destination directory does not exist.

    Returns:
      The number of changed help text files.
    """
    if not os.path.isdir(self._help_dir):
      raise HelpTextUpdateError(
          'Destination directory [%s] must exist and be searchable.' %
          self._help_dir)
    try:
      return self._Update()
    except (IOError, OSError, SystemError) as e:
      raise HelpTextUpdateError('Update failed: %s' % unicode(e))
