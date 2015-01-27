# -*- coding: utf-8 -*-
#   
# Copyright 2015 Simone Campagna
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
#

__author__ = "Simone Campagna"
__all__ = [
    'TestFileCopy',
]

import os
import unittest
import tempfile

from invoice.database.filecopy import tempcopy, backup, nocopy

class TestFileCopy(unittest.TestCase):
    CONTENT_A = """
Test file content A
===================
"""
    CONTENT_B = """
Test file content B
###################
"""
    def setUp(self):
        pass

    # backup
    def _test_backup(self, with_error):
        with tempfile.TemporaryDirectory() as tmpdir:

            filename = os.path.join(tmpdir, 'test_backup.txt')
            with open(filename, 'w') as f_out:
                f_out.write(self.CONTENT_A)

            try:
                with backup(filename) as fcm:
                    self.assertEqual(fcm.get_filename(), filename)
                    
                    with open(fcm.get_filename(), 'w') as f_out:
                        f_out.write(self.CONTENT_B)

                    if with_error:
                        dummy = 1 / 0
            except ZeroDivisionError:
                pass

            with open(filename, 'r') as f_in:
                content = f_in.read()

            if with_error:
                self.assertEqual(content, self.CONTENT_A)
            else:
                self.assertEqual(content, self.CONTENT_B)

    def test_backup_with_error(self):
        return self._test_backup(with_error=True)

    def test_backup_without_error(self):
        return self._test_backup(with_error=False)

    # tempcopy
    def _test_tempcopy(self, with_error):
        with tempfile.TemporaryDirectory() as tmpdir:

            filename = os.path.join(tmpdir, 'test_tempcopy.txt')
            with open(filename, 'w') as f_out:
                f_out.write(self.CONTENT_A)

            try:
                with tempcopy(filename) as fcm:
                    self.assertNotEqual(fcm.get_filename(), filename)
                    
                    with open(fcm.get_filename(), 'w') as f_out:
                        f_out.write(self.CONTENT_B)

                    if with_error:
                        dummy = 1 / 0
            except ZeroDivisionError:
                pass

            with open(filename, 'r') as f_in:
                content = f_in.read()

            self.assertEqual(content, self.CONTENT_A)

    def test_tempcopy_with_error(self):
        return self._test_tempcopy(with_error=True)

    def test_tempcopy_without_error(self):
        return self._test_tempcopy(with_error=False)

    # nocopy
    def _test_nocopy(self, with_error):
        with tempfile.TemporaryDirectory() as tmpdir:

            filename = os.path.join(tmpdir, 'test_tempcopy.txt')
            with open(filename, 'w') as f_out:
                f_out.write(self.CONTENT_A)

            try:
                with nocopy(filename) as fcm:
                    self.assertEqual(fcm.get_filename(), filename)
                    
                    with open(fcm.get_filename(), 'w') as f_out:
                        f_out.write(self.CONTENT_B)

                    if with_error:
                        dummy = 1 / 0
            except ZeroDivisionError:
                pass

            with open(filename, 'r') as f_in:
                content = f_in.read()

            self.assertEqual(content, self.CONTENT_B)

    def test_nocopy_with_error(self):
        return self._test_nocopy(with_error=True)

    def test_nocopy_without_error(self):
        return self._test_nocopy(with_error=False)
