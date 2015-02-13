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
    'TestInvoiceProgram',
]

import os
import tempfile
import unittest

from invoice import files

class TestFiles(unittest.TestCase):
 
    def test_create_file_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "alpha")
            self.assertFalse(os.path.exists(subdir))
            tmpfile = os.path.join(subdir, "a.txt")
            files.create_file_dir(tmpfile)
            self.assertTrue(os.path.exists(subdir))
            
