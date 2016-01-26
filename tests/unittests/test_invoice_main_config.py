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
  + warning_mode             = ('ignore:*',)
  + error_mode               = ('ignore:*',)
  + partial_update           = True
  + remove_orphaned          = True
  + header                   = True
  + total                    = True
  + stats_group              = 'month'
  + list_field_names         = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'fee', 'refunds', 'cpa', 'taxes', 'income', 'currency')
  + show_scan_report         = False
  + table_mode               = 'text'
  + max_interruption_days    = 365
  + spy_notify_level         = 'info'
  + spy_delay                = 0.5
"""
    CONFIG_SHOW_WERROR_ERAISE = """\
configuration:
  + warning_mode             = ('error:*',)
  + error_mode               = ('raise:*',)
  + partial_update           = True
  + remove_orphaned          = True
  + header                   = True
  + total                    = True
  + stats_group              = 'month'
  + list_field_names         = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'fee', 'refunds', 'cpa', 'taxes', 'income', 'currency')
  + show_scan_report         = False
  + table_mode               = 'text'
  + max_interruption_days    = 365
  + spy_notify_level         = 'info'
  + spy_delay                = 0.5
"""
    CONFIG_SHOW_PARTIAL_UPDATE_ON = """\
configuration:
  + warning_mode             = ('log:*',)
  + error_mode               = ('log:*',)
  + partial_update           = True
  + remove_orphaned          = True
  + header                   = True
  + total                    = True
  + stats_group              = 'month'
  + list_field_names         = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'fee', 'refunds', 'cpa', 'taxes', 'income', 'currency')
  + show_scan_report         = False
  + table_mode               = 'text'
  + max_interruption_days    = 365
  + spy_notify_level         = 'info'
  + spy_delay                = 0.5
"""
    CONFIG_SHOW_PARTIAL_UPDATE_OFF = """\
configuration:
  + warning_mode             = ('log:*',)
  + error_mode               = ('log:*',)
  + partial_update           = False
  + remove_orphaned          = True
  + header                   = True
  + total                    = True
  + stats_group              = 'month'
  + list_field_names         = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'fee', 'refunds', 'cpa', 'taxes', 'income', 'currency')
  + show_scan_report         = False
  + table_mode               = 'text'
  + max_interruption_days    = 365
  + spy_notify_level         = 'info'
  + spy_delay                = 0.5
"""
    CONFIG_SHOW_MIX = """\
configuration:
  + warning_mode             = ('error:*', 'log:005')
  + error_mode               = ('raise:009',)
  + partial_update           = True
  + remove_orphaned          = True
  + header                   = True
  + total                    = True
  + stats_group              = 'week'
  + list_field_names         = ('tax_code', 'city', 'number', 'income')
  + show_scan_report         = True
  + table_mode               = 'text'
  + max_interruption_days    = 361
  + spy_notify_level         = 'info'
  + spy_delay                = 0.32
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
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['version', '-R', rc_dir],
            )
            self.assertEqual(p.string(), self.VERSION_OUTPUT)

    def test_invoice_main_config_werror_eraise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '-werror', '-eraise'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_WERROR_ERAISE)

    def test_invoice_main_config_wignore_eignore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '-wignore', '-eignore'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_WIGNORE_EIGNORE)

    def test_invoice_main_config_partial_update_on(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=on'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_partial_update_off(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=off'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)

    def test_invoice_main_config_partial_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_init_config_var(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc'), '-gweek', '-s'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update', '--fields=codice_fiscale,città,numero,incasso', '-b', '-I', '361', '-w', 'error:*', 'log:005', '-e', 'raise:009', '-sl', 'info', '-sd','0.32'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_MIX)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-R', rc_dir],
            )
            self.assertEqual(p.string(), """\
#fatture aggiunte: 6
#fatture modificate: 0
#fatture rimosse: 0
ultima fattura inserita per ciascun anno:
-----------------------------------------
codice_fiscale   città      numero incasso
KNTCRK01G01H663X Smallville      6  246.66
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663S 2014      1
PRKPRT01G01H663M 2014      2
BNNBRC01G01H663S 2014      3
WNYBRC01G01H663S 2014      4
KNTCRK01G01H663X 2014      5
KNTCRK01G01H663X 2014      6
""")
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   città         numero incasso
WNYBRC01G01H663S Gotham City        1   51.00
PRKPRT01G01H663M New York City      2   76.50
BNNBRC01G01H663S Greenville         3  102.00
WNYBRC01G01H663S Gotham City        4   51.00
KNTCRK01G01H663X Smallville         5  153.00
KNTCRK01G01H663X Smallville         6  246.66
""")

    def test_invoice_main_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_reset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=off'],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--reset'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_import_export(self):
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.NamedTemporaryFile() as p_file:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )   
            self.assertEqual(p.string(), '') 

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=on'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--export', p_file.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)
            p_file.flush()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=off'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--import', p_file.name],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_patterns_edit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['init', '-R', rc_dir, os.path.join(self.dirname, '*.doc')],
            )   
            self.assertEqual(p.string(), '') 

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--partial-update=on'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['config', '-R', rc_dir, '--edit', '--editor', 'sed "s/partial_update *= *True/partial_update = False/g" -i'],
            )   
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)


