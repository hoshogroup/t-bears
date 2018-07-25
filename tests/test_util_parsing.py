# Copyright 2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import shutil

from tbears.command.command_util import CommandUtil
from tbears.tbears_exception import TBearsCommandException

from tests.test_command_parsing import TestCommand


class TestCommandUtil(TestCommand):
    def setUp(self):
        super().setUp()
        self.tear_down_params = {'proj_unittest': 'file', 'proj_unittest_dir': 'dir'}
        self.project = 'proj_unittest'
        self.score_class = 'TestClass'

    # Test if cli arguments are parced correctly.
    def test_init_args_parsing(self):
        # Parsing test
        cmd = f'init {self.project} {self.score_class}'
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(parsed.command, 'init')
        self.assertEqual(parsed.project, self.project)
        self.assertEqual(parsed.score_class, self.score_class)

        # Insufficient argument
        cmd = f'init {self.project}'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())

    def test_init_necessary_and_correct_args(self):
        project_dir = 'proj_unittest_dir'

        # Correct project name and class name
        cmd = f'init {self.project} {self.score_class}'
        parsed = self.parser.parse_args(cmd.split())
        try:
            CommandUtil._check_init(vars(parsed))
        except:
            exception_raised = True
        else:
            exception_raised = False
        self.assertFalse(exception_raised)

        # Project and score_class are same
        cmd = f'init {self.project} {self.project}'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandUtil._check_init, vars(parsed))

        # Input existing SCORE path when initializing the SCORE
        cmd = f'init {self.project} {self.score_class}'
        self.touch(self.project)
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandUtil._check_init, vars(parsed))
        os.remove(self.project)

        # Input existing SCORE directory when initializing the SCORE.
        cmd = f'init {project_dir} {self.score_class}'
        os.mkdir(project_dir)
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandUtil._check_init, vars(parsed))
        shutil.rmtree(project_dir)

        # Input right path (path should equal to ./{project name}/package.json "main_file" property)
        cmd = f'init {self.project} {self.score_class}'
        parsed = self.parser.parse_args(cmd.split())
        self.cmd.cmdUtil.init(conf=vars(parsed))
        with open(f'{self.project}/package.json', mode='r') as package_contents:
            package_json = json.loads(package_contents.read())
        main = package_json['main_file']
        self.assertEqual(self.project, main)
        shutil.rmtree(self.project)

    def test_samples_args_parsing(self):
        # Parsing test
        cmd = f'samples'
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(parsed.command, 'samples')

        # Too much argument
        cmd = f'samples arg1 arg2'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
