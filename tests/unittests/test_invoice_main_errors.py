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
    'Test_invoice_main',
]

import datetime
import glob
import os
import sys
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.invoice_main import invoice_main
from invoice.invoice_db import InvoiceDb
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter
from invoice.error import InvoiceSyntaxError

class Test_invoice_main(unittest.TestCase):
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_invalid_fields(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            with self.assertRaises(SystemExit) as cm:
                p.reset()
                invoice_main(
                    printer=p,
                    logger=self.logger,
                    args=['-d', db_filename.name, 'list', '--fields', 'tax_code,missing_field'],
                )

    def test_invoice_main_invalid_onoff(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            with self.assertRaises(SystemExit) as cm:
                invoice_main(
                    printer=p,
                    logger=self.logger,
                    args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc'), '--partial-update=disabled'],
                )

    def test_invoice_main_invalid_filter(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--filter', 'città = "Rome"'],
            )
