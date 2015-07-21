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
    'Test_invoice_main_stats',
]

import datetime
import os
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_main import invoice_main
from invoice.invoice_db import InvoiceDb
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter

class Test_invoice_main_stats_client(unittest.TestCase):
    STATS_CLIENT_2014_365 = """\
WNYBRC01G01H663S 2014-01-03 2014-01-25 Bruce Wayne <---> 2 102.00 100.00%
"""
    STATS_CLIENT_2014_90 = """\
WNYBRC01G01H663S 2014-01-03 2014-01-25 Bruce Wayne [---] 2 102.00 100.00%
"""
    STATS_CLIENT_10_27_365 = """\
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne <---> 1 51.00 100.00%
"""
    STATS_CLIENT_10_27_90 = """\
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne <---] 1 51.00 100.00%
"""
    STATS_CLIENT_10_27_1 = """\
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne [---] 1 51.00 100.00%
"""
    STATS_CLIENT_01_10_365 = """\
WNYBRC01G01H663S 2014-01-03 2014-01-03 Bruce Wayne <---> 1 51.00 100.00%
"""
    STATS_CLIENT_01_10_90 = """\
WNYBRC01G01H663S 2014-01-03 2014-01-03 Bruce Wayne [---> 1 51.00 100.00%
"""
    STATS_CLIENT_01_10_1 = """\
WNYBRC01G01H663S 2014-01-03 2014-01-03 Bruce Wayne [---] 1 51.00 100.00%
"""


    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def _test_invoice_main_stats_client(self, output, max_interruption_days=365, options=None):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            p.reset()
            args = ['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'test_wayne_continuation', '*.doc')]
            if max_interruption_days is not None:
                args.append('--max-interruption-days={}'.format(max_interruption_days))
            invoice_main(
                printer=p,
                args=args,
                logger=self.logger,
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            #args=['-d', db_filename.name, 'stats', '-S', '2014-01-10', '-E', '2014-01-27']
            args=['-d', db_filename.name, 'stats', '-gclient', '--total=off', '--header=off', '-C', 'WNYBRC01G01H663S']
            if options:
                args.extend(options)
            invoice_main(
                printer=p,
                logger=self.logger,
                args=args,
            )
            self.assertEqual(p.string(), output)

    def test_invoice_main_stats_client_2014_365(self):
        return self._test_invoice_main_stats_client(options=['-y', '2014'], output=self.STATS_CLIENT_2014_365, max_interruption_days=365)

    def test_invoice_main_stats_client_2014_90(self):
        return self._test_invoice_main_stats_client(options=['-y', '2014'], output=self.STATS_CLIENT_2014_90, max_interruption_days=90)

    def test_invoice_main_stats_client_10_27_365(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-10', '-E', '2014-01-27'], output=self.STATS_CLIENT_10_27_365, max_interruption_days=365)

    def test_invoice_main_stats_client_10_27_90(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-10', '-E', '2014-01-27'], output=self.STATS_CLIENT_10_27_90, max_interruption_days=90)

    def test_invoice_main_stats_client_10_27_1(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-10', '-E', '2014-01-27'], output=self.STATS_CLIENT_10_27_1, max_interruption_days=1)

    def test_invoice_main_stats_client_01_10_365(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-01', '-E', '2014-01-10'], output=self.STATS_CLIENT_01_10_365, max_interruption_days=365)

    def test_invoice_main_stats_client_01_10_90(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-01', '-E', '2014-01-10'], output=self.STATS_CLIENT_01_10_90, max_interruption_days=90)

    def test_invoice_main_stats_client_01_10_1(self):
        return self._test_invoice_main_stats_client(options=['-S', '2014-01-01', '-E', '2014-01-10'], output=self.STATS_CLIENT_01_10_1, max_interruption_days=1)


