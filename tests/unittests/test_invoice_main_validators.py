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
from invoice.version import VERSION

class Test_invoice_main_config(unittest.TestCase):
    VALIDATORS_SHOW_EMPTY = """\
validators:
"""
    VALIDATORS_SHOW_EXAMPLE = """\
validators:
  + filter:  'Date("2014-01-01") <= date <= Date("2014-12-31")'
    check:   'not date.weekday() in {Weekday["Saturday"], Weekday["Sunday"]}'
    message: 'invalid weekday for year 2014'
"""

    LIST_SHORT = """\
anno numero città         data       codice_fiscale   nome                incasso valuta
2014      1 Gotham City   2014-01-03 WNYBRC01G01H663S Bruce Wayne           51.00 euro  
2014      2 New York City 2014-01-03 PRKPRT01G01H663M Peter B. Parker       76.50 euro  
2014      3 Greenville    2014-01-22 BNNBRC01G01H663S Robert Bruce Banner  102.00 euro  
"""
    LIST_FULL = LIST_SHORT + """\
2014      4 Gotham City   2014-01-25 WNYBRC01G01H663S Bruce Wayne           51.00 euro  
2014      5 Smallville    2014-01-29 KNTCRK01G01H663X Clark Kent           153.00 euro  
2014      6 Smallville    2014-02-28 KNTCRK01G01H663X Clark Kent           216.66 euro  
"""
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_validators_scan(self):
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
                args=['validators', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EMPTY)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--add', 'Date("2014-01-01") <= date <= Date("2014-12-31")', 'not date.weekday() in {Weekday["Saturday"], Weekday["Sunday"]}', 'invalid weekday for year 2014'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-d', db_filename.name]
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-d', db_filename.name]
            )
            self.assertEqual(p.string(), self.LIST_SHORT)

    def test_invoice_main_validators_validate(self):
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
                args=['scan', '-d', db_filename.name],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.LIST_FULL)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--add', 'Date("2014-01-01") <= date <= Date("2014-12-31")', 'not date.weekday() in {Weekday["Saturday"], Weekday["Sunday"]}', 'invalid weekday for year 2014'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validate', '-d', db_filename.name],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.LIST_SHORT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-d', db_filename.name],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.LIST_SHORT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--clear'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EMPTY)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-d', db_filename.name],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-d', db_filename.name],
            )
            #self.assertEqual(p.string(), self.LIST_SHORT)
#
#            p.reset()
#            invoice_main(
#                printer=p,
#                logger=self.logger,
#                args=['scan', '-d', db_filename.name, '--force-refresh'],
#            )
#
#            p.reset()
#            invoice_main(
#                printer=p,
#                logger=self.logger,
#                args=['list', '-d', db_filename.name],
#            )
            self.assertEqual(p.string(), self.LIST_FULL)

    def test_invoice_main_validators_import_export(self):
        with tempfile.NamedTemporaryFile() as db_filename, tempfile.NamedTemporaryFile() as v_filename:
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
                args=['validators', '-d', db_filename.name, '--add', 'Date("2014-01-01") <= date <= Date("2014-12-31")', 'not date.weekday() in {Weekday["Saturday"], Weekday["Sunday"]}', 'invalid weekday for year 2014'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--export', v_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--clear'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EMPTY)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--import', v_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

    def test_invoice_main_validators_edit(self):
        with tempfile.NamedTemporaryFile() as db_filename, tempfile.NamedTemporaryFile() as v_filename:
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
                args=['validators', '-d', db_filename.name, '--add', 'Date("2014-01-01") <= date <= Date("2014-12-31")', 'not date.weekday() in {Weekday["Saturday"], Weekday["Sunday"]}', 'invalid weekday for year 2014'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validators', '-d', db_filename.name, '--edit', '--editor', 'sed "s/2014/2028/g" -i'],
            )
            self.assertEqual(p.string(), self.VALIDATORS_SHOW_EXAMPLE.replace('2014', '2028'))


