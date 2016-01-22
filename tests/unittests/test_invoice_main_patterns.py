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
    'Test_invoice_main_config',
]

import datetime
import glob
import os
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_main import invoice_main
from invoice.invoice_db import InvoiceDb
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter

class Test_invoice_main_patterns(unittest.TestCase):
    PATTERNS_CLEAR = """\
patterns:
"""

    PATTERNS_DEFAULT = """\
patterns:
  + Pattern(pattern='<DIRNAME>/*.doc', skip=False)
"""

    PATTERNS_ADD_REMOVE = """\
patterns:
  + Pattern(pattern='<DIRNAME>/*.doc', skip=False)
  + Pattern(pattern='<DIRNAME>/*.Doc', skip=True)
  + Pattern(pattern='<DIRNAME>/*.DOC', skip=False)
"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_patterns_add_remove(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-d', db_filename.name, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '-a', '!example/*.Doc', '-a', 'example/*.DOC'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '-x', '!example/*.Doc', '-x', 'example/*.DOC'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_DEFAULT)

            # check if duplicate pattern raises:
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '-a', 'example/*.doc'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_DEFAULT)

    def test_invoice_main_patterns_clear(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-d', db_filename.name, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--clear'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_CLEAR)

    def test_invoice_main_patterns_warning(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-d', db_filename.name] + list(glob.glob(os.path.join(self.dirname, '*.doc'))),
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--clear'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_CLEAR)

    def test_invoice_main_patterns_import_export(self):
        with tempfile.NamedTemporaryFile() as db_filename, tempfile.NamedTemporaryFile() as p_file:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-d', db_filename.name, os.path.join(self.dirname, '*.doc')],
            )   
            self.assertEqual(p.string(), '') 

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '-a', '!example/*.Doc', '-a', 'example/*.DOC'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--export', p_file.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)
            p_file.flush()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--clear'],
            )
            self.assertEqual(p.string(), self.PATTERNS_CLEAR)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--import', p_file.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

    def test_invoice_main_patterns_edit(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-d', db_filename.name, os.path.join(self.dirname, '*.doc')],
            )   
            self.assertEqual(p.string(), '') 

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '-a', '!example/*.Doc', '-a', 'example/*.DOC'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['patterns', '-d', db_filename.name, '--edit', '--editor', 'sed "s/DOC/docx/g" -i'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE.replace('DOC', 'docx'))


