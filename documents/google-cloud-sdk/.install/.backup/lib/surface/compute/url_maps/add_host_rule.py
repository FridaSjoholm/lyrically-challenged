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

"""Command for adding a host rule to a URL map."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.url_maps import flags


class AddHostRule(base_classes.ReadWriteCommand):
  """Add a rule to a URL map to map hosts to a path matcher."""

  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description for the host rule.')

    hosts = parser.add_argument(
        '--hosts',
        type=arg_parsers.ArgList(min_length=1),
        metavar='HOST',
        required=True,
        help='The set of hosts to match requests against.')
    hosts.detailed_help = """\
        The set of hosts to match requests against. Each host must be
        a fully qualified domain name (FQDN) with the exception that
        the host can begin with a ``*'' or ``*-''. ``*'' acts as a
        glob and will match any string of atoms to the left where an
        atom is separated by dots (``.'') or dashes (``-'').
        """

    path_matcher = parser.add_argument(
        '--path-matcher-name',
        required=True,
        help=('The name of the patch matcher to use if a request matches this '
              'host rule.'))
    path_matcher.detailed_help = """\
        The name of the patch matcher to use if a request matches this
        host rule. The patch matcher must already exist in the URL map
        (see `gcloud compute url-maps add-path-matcher`).
        """

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def resource_type(self):
    return 'urlMaps'

  def CreateReference(self, args):
    return self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

  def GetGetRequest(self, args):
    """Returns the request for the existing URL map resource."""
    return (self.service,
            'Get',
            self.messages.ComputeUrlMapsGetRequest(
                urlMap=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeUrlMapsUpdateRequest(
                urlMap=self.ref.Name(),
                urlMapResource=replacement,
                project=self.project))

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = copy.deepcopy(existing)

    new_host_rule = self.messages.HostRule(
        description=args.description,
        hosts=sorted(args.hosts),
        pathMatcher=args.path_matcher_name)

    replacement.hostRules.append(new_host_rule)

    return replacement


AddHostRule.detailed_help = {
    'brief': 'Add a rule to a URL map to map hosts to a path matcher',
    'DESCRIPTION': """\
        *{command}* is used to add a mapping of hosts to a patch
        matcher in a URL map. The mapping will match the host
        component of HTTP requests to path matchers which in turn map
        the request to a backend service. Before adding a host rule,
        at least one path matcher must exist in the URL map to take
        care of the path component of the requests.
        `gcloud compute url-maps add-path-matcher` or
        `gcloud compute url-maps edit` can be used to add path matchers.
        """,
    'EXAMPLES': """\
        To create a host rule mapping the ```*-foo.google.com``` and
        ```google.com``` hosts to the ```www``` path matcher, run:

          $ {command} MY-URL-MAP --hosts '*-foo.google.com,google.com' --path-matcher-name www
        """,
}
