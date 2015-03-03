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
    CONFIG_SHOW_WIGNORE_EIGNORE = """\
configuration:
  + warning_mode         = 'ignore'
  + error_mode           = 'ignore'
  + partial_update       = True
  + remove_orphaned      = True
  + header               = True
  + total                = True
  + stats_group          = 'month'
  + list_field_names     = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
  + show_scan_report     = False
"""
    CONFIG_SHOW_WERROR_ERAISE = """\
configuration:
  + warning_mode         = 'error'
  + error_mode           = 'raise'
  + partial_update       = True
  + remove_orphaned      = True
  + header               = True
  + total                = True
  + stats_group          = 'month'
  + list_field_names     = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
  + show_scan_report     = False
"""
    CONFIG_SHOW_PARTIAL_UPDATE_ON = """\
configuration:
  + warning_mode         = 'log'
  + error_mode           = 'log'
  + partial_update       = True
  + remove_orphaned      = True
  + header               = True
  + total                = True
  + stats_group          = 'month'
  + list_field_names     = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
  + show_scan_report     = False
"""
    CONFIG_SHOW_PARTIAL_UPDATE_OFF = """\
configuration:
  + warning_mode         = 'log'
  + error_mode           = 'log'
  + partial_update       = False
  + remove_orphaned      = True
  + header               = True
  + total                = True
  + stats_group          = 'month'
  + list_field_names     = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
  + show_scan_report     = False
"""
    CONFIG_SHOW_MIX = """\
configuration:
  + warning_mode         = 'log'
  + error_mode           = 'log'
  + partial_update       = True
  + remove_orphaned      = True
  + header               = True
  + total                = True
  + stats_group          = 'week'
  + list_field_names     = ('tax_code', 'city', 'number', 'income')
  + show_scan_report     = True
"""

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

    VERSION_OUTPUT = """\
versione del programma: {}
versione del database:  {}
""".format(VERSION, VERSION)

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_version(self):
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
                args=['-d', db_filename.name, 'version'],
            )
            self.assertEqual(p.string(), self.VERSION_OUTPUT)

    def test_invoice_main_config_werror_eraise(self):
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
                args=['-d', db_filename.name, 'config', '-werror', '-eraise'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_WERROR_ERAISE)

    def test_invoice_main_config_wignore_eignore(self):
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
                args=['-d', db_filename.name, 'config', '-wignore', '-eignore'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_WIGNORE_EIGNORE)

    def test_invoice_main_config_partial_update_on(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update=on'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_partial_update_off(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update=off'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)

    def test_invoice_main_config_partial_update(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_init_config_var(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc'), '-gweek', '-s'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'config', '--partial-update', '--fields=codice_fiscale,città,numero,incasso', '-b'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_MIX)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), """\
ultima fattura inserita per ciascun anno:
-----------------------------------------
codice_fiscale   città      numero incasso
KNTCRK01G01H663X Smallville      5  152.50
""")

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
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   città         numero incasso
WNYBRC01G01H663S Gotham City        1   51.00
PRKPRT01G01H663M New York City      2   76.50
BNNBRC01G01H663S Greenville         3  102.00
WNYBRC01G01H663S Gotham City        4   51.00
KNTCRK01G01H663X Smallville         5  152.50
""")

    def test_invoice_main_config(self):
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
                args=['-d', db_filename.name, 'config'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_reset(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update=off'],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'config', '--reset'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_patterns_add_remove(self):
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
                args=['-d', db_filename.name, 'patterns', '-a', '!example/*.Doc', '-a', 'example/*.DOC'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '-x', '!example/*.Doc', '-x', 'example/*.DOC'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_DEFAULT)

            # check if duplicate pattern raises:
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '-a', 'example/*.doc'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_DEFAULT)

    def test_invoice_main_patterns_clear(self):
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
                args=['-d', db_filename.name, 'patterns', '--clear'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_CLEAR)

    def test_invoice_main_patterns_warning(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init'] + list(glob.glob(os.path.join(self.dirname, '*.doc'))),
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '--clear'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_CLEAR)

    def test_invoice_main_patterns_import_export(self):
        with tempfile.NamedTemporaryFile() as db_filename, tempfile.NamedTemporaryFile() as p_filename:
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
                args=['-d', db_filename.name, 'patterns', '-a', '!example/*.Doc', '-a', 'example/*.DOC'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '--export', p_filename.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '--clear'],
            )
            self.assertEqual(p.string(), self.PATTERNS_CLEAR)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'patterns', '--import', p_filename.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.PATTERNS_ADD_REMOVE)

