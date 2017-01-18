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

"""A command that validates gcloud flags according to Cloud SDK CLI Style."""

import os
import StringIO

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class UnknownCheckException(Exception):
  """An exception when unknown lint check is requested."""


class LintException(exceptions.Error):
  """One or more lint errors found."""


class LintError(object):
  """Validation failure.

  Attributes:
    name: str, The name of the validation that produced this failure.
    command: calliope.backend.CommandCommon, The offending command.
    msg: str, A message indicating what the problem was.
  """

  def __init__(self, name, command, error_message):
    self.name = name
    self.command = command
    self.msg = '[{cmd}]: {msg}'.format(
        cmd='.'.join(command.GetPath()), msg=error_message)


class Checker(object):
  """The abstract base class for all the checks.

  Attributes:
    name: A string, the name of this Checker.
    description: string, command line description of this check.
  """

  def ForEveryGroup(self, group):
    pass

  def ForEveryCommand(self, command):
    pass

  def End(self):
    return []


class NameChecker(Checker):
  """Checks if group,command and flags names have underscores or mixed case."""

  name = 'NameCheck'
  description = 'Verifies all existing flags not to have underscores.'

  def __init__(self):
    super(NameChecker, self).__init__()
    self._issues = []

  def _ForEvery(self, cmd_or_group):
    """Run name check for given command or group."""

    if '_' in cmd_or_group.cli_name:
      self._issues.append(LintError(
          name=NameChecker.name,
          command=cmd_or_group,
          error_message='command name [{0}] has underscores'.format(
              cmd_or_group.cli_name)))

    if not (cmd_or_group.cli_name.islower() or cmd_or_group.cli_name.isupper()):
      self._issues.append(LintError(
          name=NameChecker.name,
          command=cmd_or_group,
          error_message='command name [{0}] mixed case'.format(
              cmd_or_group.cli_name)))

    for flag in cmd_or_group.GetSpecificFlags():
      if not any(f.startswith('--') for f in flag.option_strings):
        if len(flag.option_strings) != 1 or flag.option_strings[0] != '-h':
          self._issues.append(LintError(
              name=NameChecker.name,
              command=cmd_or_group,
              error_message='flag [{0}] has no long form'.format(
                  ','.join(flag.option_strings))))
      for flag_option_string in flag.option_strings:
        msg = None
        if '_' in flag_option_string:
          msg = 'flag [%s] has underscores' % flag_option_string
        if (flag_option_string.startswith('--')
            and not flag_option_string.islower()):
          msg = 'long flag [%s] has upper case characters' % flag_option_string
        if msg:
          self._issues.append(LintError(
              name=NameChecker.name, command=cmd_or_group, error_message=msg))

  def ForEveryGroup(self, group):
    self._ForEvery(group)

  def ForEveryCommand(self, command):
    self._ForEvery(command)

  def End(self):
    return self._issues


class BadListsChecker(Checker):
  """Checks command flags that take lists."""

  name = 'BadLists'
  description = 'Verifies all flags implement lists properly.'

  def __init__(self):
    super(BadListsChecker, self).__init__()
    self._issues = []

  def _ForEvery(self, cmd_or_group):
    for flag in cmd_or_group.GetSpecificFlags():
      if flag.nargs not in [None, 0, 1]:
        self._issues.append(LintError(
            name=BadListsChecker.name,
            command=cmd_or_group,
            error_message=(
                'flag [{flg}] has nargs={nargs}'.format(
                    flg=flag.option_strings[0],
                    nargs=repr(flag.nargs)))))
      if isinstance(flag.type, arg_parsers.ArgType):
        if not flag.metavar:
          self._issues.append(LintError(
              name=BadListsChecker.name,
              command=cmd_or_group,
              error_message=(
                  'list flag [{flg}] has no metavar'.format(
                      flg=flag.option_strings[0]))))

  def ForEveryGroup(self, group):
    self._ForEvery(group)

  def ForEveryCommand(self, command):
    self._ForEvery(command)

  def End(self):
    return self._issues


def _GetWhitelistedCommandVocabulary():
  """Returns whitelisted set of gcloud commands."""

  vocabulary_file = os.path.join(os.path.dirname(__file__),
                                 'gcloud_command_vocabulary.txt')
  with open(vocabulary_file, 'r') as f:
    return set(line for line in f.read().split('\n')
               if not line.startswith('#'))


class VocabularyChecker(Checker):
  """Checks that command is the list of whitelisted names."""

  name = 'WhitelistedNameCheck'
  description = 'Verifies that every command is whitelisted.'

  def __init__(self):
    super(VocabularyChecker, self).__init__()
    self._whitelist = _GetWhitelistedCommandVocabulary()
    self._issues = []

  def ForEveryGroup(self, group):
    pass

  def ForEveryCommand(self, command):
    if command.cli_name not in self._whitelist:
      self._issues.append(LintError(
          name=self.name,
          command=command,
          error_message='command name [{0}] is not whitelisted'.format(
              command.cli_name)))

  def End(self):
    return self._issues


def _WalkGroupTree(group):
  """Visits each group in the CLI group tree.

  Args:
    group: backend.CommandGroup, root CLI subgroup node.
  Yields:
    group instance.
  """

  yield group

  for sub_group in group.groups.itervalues():
    for value in _WalkGroupTree(sub_group):
      yield value


class Linter(object):
  """Lints gcloud commands."""

  def __init__(self):
    self._checks = []

  def AddCheck(self, check):
    self._checks.append(check())

  def Run(self, group_root):
    """Runs registered checks on all groups and commands."""
    for group in _WalkGroupTree(group_root):
      for check in self._checks:
        check.ForEveryGroup(group)
      for command in group.commands.itervalues():
        for check in self._checks:
          check.ForEveryCommand(command)

    return [issue for check in self._checks for issue in check.End()]


# List of registered checks, all are run by default.
_DEFAULT_LINT_CHECKS = [
    NameChecker,
]

_LINT_CHECKS = [
    BadListsChecker,
    VocabularyChecker,
]


def _FormatCheckList(check_list):
  buf = StringIO.StringIO()
  for check in check_list:
    usage_text.WrapWithPrefix(
        check.name, check.description, 20, 78, '  ', writer=buf)
  return buf.getvalue()


class Lint(base.Command):
  """Validate gcloud flags according to Cloud SDK CLI Style."""

  @staticmethod
  def Args(parser):
    checks_arg = parser.add_argument(
        'checks',
        metavar='CHECKS',
        nargs='*',
        default=[],
        help='Restrict validation to the specified checks.')
    checks_arg.detailed_help = """\
A list of checks to apply to gcloud groups and commands.
If omitted will run all available checks.
Available Checks:
""" + _FormatCheckList(_LINT_CHECKS)

  def Run(self, args):
    # pylint: disable=protected-access
    group = self.cli._TopElement()
    group.LoadAllSubElements(recursive=True)
    return Lint._SetupAndRun(group, args.checks)

  @staticmethod
  def _SetupAndRun(group, check_list):
    """Builds up linter and executes it for given set of checks."""

    linter = Linter()
    unknown_checks = []
    if not check_list:
      for check in _DEFAULT_LINT_CHECKS:
        linter.AddCheck(check)
    else:
      available_checkers = dict(
          (checker.name, checker)
          for checker in _DEFAULT_LINT_CHECKS + _LINT_CHECKS)
      for check in check_list:
        if check in available_checkers:
          linter.AddCheck(available_checkers[check])
        else:
          unknown_checks.append(check)

    if unknown_checks:
      raise UnknownCheckException(
          'Unknown lint checks: %s' % ','.join(unknown_checks))

    return linter.Run(group)

  def Display(self, args, result):
    writer = log.out
    for issue in result:
      writer.Print(issue.msg)
    if result:
      raise LintException('there were some lint errors.')
