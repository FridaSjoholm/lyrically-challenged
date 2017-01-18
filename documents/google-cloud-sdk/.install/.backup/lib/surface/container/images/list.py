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
"""List images command."""

from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import http
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List existing images."""

  detailed_help = {
      'DESCRIPTION': """\
          The container images list command of gcloud lists metadata about
          existing container images in a specified repository. Repositories
          must be hosted by the Google Container Registry.
      """,
      'EXAMPLES': """\
          List the images in a specified repository:

            $ {{command}} --repository=gcr.io/myproject

          List the images in the default repository:

            $ {{command}}

      """,
  }

  def Collection(self):
    return 'container.images'

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--repository',
        required=False,
        help=('The name of the repository. Format: *.gcr.io/repository. '
              'Defaults to gcr.io/<project>, for the active project.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    repository_arg = args.repository
    if not repository_arg:
      repository_arg = 'gcr.io/{0}'.format(
          properties.VALUES.core.project.Get(required=True))

    # Throws if invalid.
    repository = util.ValidateRepositoryPath(repository_arg)

    def _DisplayName(c):
      """Display the fully-qualified name."""
      return '{0}/{1}'.format(repository, c)

    http_obj = http.Http()
    with docker_image.FromRegistry(basic_creds=util.CredentialProvider(),
                                   name=repository,
                                   transport=http_obj) as r:
      images = [{'name': _DisplayName(c)} for c in r.children()]
      return images
