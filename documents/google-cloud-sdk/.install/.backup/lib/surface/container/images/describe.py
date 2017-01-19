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
"""Command to show Container Analysis Data for a specified image."""

from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base

# Add to this as we add more container analysis data.
_DEFAULT_KINDS = [
    'BUILD_DETAILS',
    'PACKAGE_VULNERABILITY',
    'IMAGE_BASIS'
]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Lists container analysis data for a given image.

  Lists container analysis data for a valid image.

  ## EXAMPLES

  Describe container analysis data for a specified image:

    $ {{command}} gcr.io/myproject/myimage@digest
  """

  def Collection(self):
    return 'container.images'

  def Format(self, unused_args):
    return 'object'

  @staticmethod
  def Args(parser):
    parser.add_argument('image',
                        help=('The fully qualified image '
                              'reference to describe.\n'
                              '*.gcr.io/repository@digest'))
    parser.add_argument('--occurrence-filter',
                        default=' OR '.join(['kind = "{kind}"'.format(kind=x)
                                             for x in _DEFAULT_KINDS]),
                        help=('Additional filter to fetch occurrences for '
                              'a given fully qualified image reference.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      Some value that we want to have printed later.
    """

    img_name = util.GetDigestFromName(args.image)

    return util.TransformContainerAnalysisData(
        img_name, args.occurrence_filter)
