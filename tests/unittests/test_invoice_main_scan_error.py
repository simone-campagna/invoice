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
    'Test_invoice_main_scan_error',
]

import datetime
import glob
import os
import shutil
import sys
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_main import invoice_main
from invoice.invoice_db import InvoiceDb
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter

class Test_invoice_main_scan_error(unittest.TestCase):
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_err(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_wrong_number', '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663S 2014      1
PRKPRT01G01H663M 2014      2
BNNBRC01G01H663S 2014      3
WNYBRC01G01H663S 2014      4
KNTCRK01G01H663X 2014      5
""")

    def test_invoice_main_err_partial_update_off(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', '--partial-update=off', os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_wrong_number', '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), '')

    def _test_invoice_main_err_changed_invoice(self, subdir, output):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            data_dir = os.path.join(tmpdir, 'data')
            os.makedirs(data_dir)

            for f in glob.glob(os.path.join(self.dirname, '*.doc')):
                shutil.copyfile(f, os.path.join(data_dir, os.path.basename(f)))

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'init', os.path.join(data_dir, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'list', '--fields', 'tax_code,year,number,date'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero data      
WNYBRC01G01H663S 2014      1 2014-01-03
PRKPRT01G01H663M 2014      2 2014-01-03
BNNBRC01G01H663S 2014      3 2014-01-22
WNYBRC01G01H663S 2014      4 2014-01-25
KNTCRK01G01H663X 2014      5 2014-01-29
""")

            for f in glob.glob(os.path.join(self.dirname, subdir, '*.doc')):
                shutil.copyfile(f, os.path.join(data_dir, os.path.basename(f)))

           
    def test_invoice_main_err_changed_invoice_tax_code(self):
        self._test_invoice_main_err_changed_invoice('error_changed_invalid_tax_code', """\
codice_fiscale   anno numero data      
WNYBRC01G01H663S 2014      1 2014-01-03
""")

    def test_invoice_main_err_changed_invoice_date(self):
        self._test_invoice_main_err_changed_invoice('error_changed_date', """\
codice_fiscale   anno numero data      
WNYBRC01G01H663S 2014      1 2014-01-03
PRKPRT01G01H663M 2014      2 2014-12-03
""")

    def _test_invoice_main_err_removed_invoice(self, remove_orphaned):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            data_dir = os.path.join(tmpdir, 'data')
            os.makedirs(data_dir)

            for f in glob.glob(os.path.join(self.dirname, '*.doc')):
                shutil.copyfile(f, os.path.join(data_dir, os.path.basename(f)))

            p = StringPrinter()

            args = ['-R', rc_dir, 'init', os.path.join(data_dir, '*.doc')]
            if remove_orphaned:
                args.append("--remove-orphaned=on")
            else:
                args.append("--remove-orphaned=off")
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=args,
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'scan'],
            )
            self.assertEqual(p.string(), '')

            out_a = """\
codice_fiscale   anno numero data      
WNYBRC01G01H663S 2014      1 2014-01-03
"""
            out_b = """\
PRKPRT01G01H663M 2014      2 2014-01-03
BNNBRC01G01H663S 2014      3 2014-01-22
WNYBRC01G01H663S 2014      4 2014-01-25
KNTCRK01G01H663X 2014      5 2014-01-29
"""

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'list', '--fields', 'tax_code,year,number,date'],
            )
            self.assertEqual(p.string(), out_a + out_b)

            for f in glob.glob(os.path.join(data_dir, '20*_002*.doc')):
                os.remove(f)

           
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'scan'],
            )
            self.assertEqual(p.string(), '')

            if remove_orphaned:
                out = out_a
            else:
                out = out_a + out_b

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-R', rc_dir, 'list', '--fields', 'tax_code,year,number,date'],
            )
            self.assertEqual(p.string(), out)

    def test_invoice_main_err_removed_invoice_remove_orphaned_on(self):
        self._test_invoice_main_err_removed_invoice(remove_orphaned=True)

    def test_invoice_main_err_removed_invoice_remove_orphaned_off(self):
        self._test_invoice_main_err_removed_invoice(remove_orphaned=False)
