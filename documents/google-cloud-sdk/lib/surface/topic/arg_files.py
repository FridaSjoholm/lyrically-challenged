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

"""Gcloud test argument files supplementary help."""

from googlecloudsdk.calliope import base


class TestingArgFiles(base.TopicCommand):
  """Supplementary help for arg-files to be used with *gcloud test*."""

  detailed_help = {

      'DESCRIPTION': """\
          {description}

          All *gcloud test android run* arguments may be specified by flags on
          the command line and/or via a YAML-formatted _ARG_FILE_. The optional,
          positional ARG_SPEC argument on the command line is used to specify
          a single _ARG_FILE_:_ARG_GROUP_NAME_ pair, where _ARG_FILE_ is the
          path to the YAML argument file, and _ARG_GROUP_NAME_ is the name
          of the argument group to load and parse. The _ARG_FILE_ must
          contain valid YAML syntax or gcloud will respond with an error.

          The basic format of a YAML argument file is:

            arg-group1:
              arg1: value1  # a comment
              arg2: value2
              ...

            # Another comment
            arg-group2:
              arg3: value3
              ...

          List arguments may be specified within square brackets:

            device-ids: [Nexus5, Nexus6, Nexus9]

          or by using the alternate YAML list notation with one dash per list
          item:

            ```
            device-ids:
              - Nexus5
              - Nexus6
              - Nexus9
            ```

          If a list argument only contains a single value, you may omit the
          square brackets:

            device-ids: Nexus9

          Composition

          A special *include: [_ARG_GROUP1_, ...]* syntax allows merging or
          composition of argument groups (see *EXAMPLES* below). Included
          argument groups can *include:* other argument groups within the
          same YAML file, with unlimited nesting.

          Precedence

          An argument which appears on the command line has the highest
          precedence and will override the same argument if it is specified
          within an argument file.

          Any argument defined directly within a group will have higher
          precedence than an identical argument which is merged into that
          group using the *include:* keyword.

          """,

      'EXAMPLES': """\

          Here are the contents of a very simple YAML argument file which
          we'll assume is stored in a file named excelsior_args.yaml:

            # Run a quick 'robo' test on the 'Excelsior' app for
            # 90 seconds using only the default virtual device.
            quick-robo-test:
              app: path/to/excelsior.apk
              type: robo
              max-steps: 100
              timeout: 90s
              async: true

          To invoke this test, run:

            $ gcloud beta test android run excelsior_args.yaml:quick-robo-test

          If your app has a login screen, or has additional UI elements which
          require input text, you may specify the resource names of the Android
          target UI elements, along with their corresponding input values, in
          the 'robo-directives' map argument. In the example below,
          "username_resource" is the resource name of the username field and
          "username" is the input for that field (similarly for password).

            # Run a 'robo' test on the 'Excelsior' app with login credentials.
            robo-test-with-login:
              app: path/to/excelsior.apk
              type: robo
              robo-directives:
                username_resource: username
                password_resource: password

          Assuming the above YAML text is appended to the arg-file named
          excelsior_args.yaml, you may invode the test by running:

            $ gcloud beta test android run excelsior_args.yaml:robo-test-with-login

          Here is a slightly more complicated example which demonstrates
          composition of argument groups. Assume the following YAML text
          is appended to the arg-file shown above named excelsior_args.yaml:

            # Specify some unit tests to be run against a test matrix
            # with one device type, two Android versions, and four
            # locales, for a total of eight test variations (1*2*4).
            unit-tests:
              type: instrumentation
              app: path/to/excelsior.apk
              test: path/to/excelsior-test.apk  # the unit tests
              timeout: 10m
              device-ids: Nexus6
              include: [supported-versions, supported-locales]

            supported-versions:
              os-version-ids: [21, 22]

            supported-locales:
              locales: [en, es, fr, it]

          To invoke this test matrix, run:

            $ gcloud beta test android run excelsior_args.yaml:unit-tests

          To run these unit tests with the same locales and os-version-ids,
          but substituting a sampling of three physical Android devices
          instead of the single virtual Nexus6 device, run:

            $ gcloud beta test android run excelsior_args.yaml:unit-tests --device-ids shamu,htc_m8,g3

          In the last example, the --device-ids argument on the
          command line overrides the device-ids: specification inside the
          arg-file because command-line arguments have higher precedence.
          """,
      }
