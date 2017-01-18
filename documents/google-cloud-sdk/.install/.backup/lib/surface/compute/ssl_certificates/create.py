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
"""Command for creating SSL certificates."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import file_utils
from googlecloudsdk.command_lib.compute.ssl_certificates import flags


class Create(base_classes.BaseAsyncCreator):
  """Create a Google Compute Engine SSL certificate.

  *{command}* is used to create SSL certificates which can be used to
  configure a target HTTPS proxy. An SSL certificate consists of a
  certificate and private key. The private key is encrypted before it is
  stored.
  """

  SSL_CERTIFICATE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_CERTIFICATE_ARG = flags.SslCertificateArgument()
    cls.SSL_CERTIFICATE_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description for the SSL certificate.')

    certificate = parser.add_argument(
        '--certificate',
        required=True,
        metavar='LOCAL_FILE_PATH',
        help='The path to a local certificate file.')
    certificate.detailed_help = """\
        The path to a local certificate file. The certificate must be in PEM
        format.  The certificate chain must be no greater than 5 certs long. The
        chain must include at least one intermediate cert.
        """

    private_key = parser.add_argument(
        '--private-key',
        required=True,
        metavar='LOCAL_FILE_PATH',
        help='The path to a local private key file.')
    private_key.detailed_help = """\
        The path to a local private key file. The private key must be in PEM
        format and must use RSA or ECDSA encryption.
        """

  @property
  def service(self):
    return self.compute.sslCertificates

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'sslCertificates'

  def CreateRequests(self, args):
    """Returns the request necessary for adding the SSL certificate."""

    ssl_certificate_ref = self.SSL_CERTIFICATE_ARG.ResolveAsResource(
        args, self.resources)
    certificate = file_utils.ReadFile(args.certificate, 'certificate')
    private_key = file_utils.ReadFile(args.private_key, 'private key')

    request = self.messages.ComputeSslCertificatesInsertRequest(
        sslCertificate=self.messages.SslCertificate(
            name=ssl_certificate_ref.Name(),
            certificate=certificate,
            privateKey=private_key,
            description=args.description),
        project=self.project)

    return [request]
