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

class Test_invoice_main_stats(unittest.TestCase):
    STATS_YEAR_NO_TOTAL = """\
anno        da:         a: #clienti #fatture incasso %incasso
2014 2014-01-10 2014-01-27        2        2  153.00  100.00%
"""
    STATS_YEAR_TOTAL = """\
anno          da:         a: #clienti #fatture incasso %incasso
2014   2014-01-10 2014-01-27        2        2  153.00  100.00%
TOTALE                              2        2  153.00  100.00%
"""
    STATS_YEAR_DEFAULT = STATS_YEAR_TOTAL

    STATS_MONTH_NO_TOTAL = """\
mese           da:         a: #clienti #fatture incasso %incasso
2014-01 2014-01-10 2014-01-27        2        2  153.00  100.00%
"""

    STATS_MONTH_TOTAL = STATS_MONTH_NO_TOTAL + """\
TOTALE                               2        2  153.00  100.00%
"""
    STATS_MONTH_DEFAULT = STATS_MONTH_TOTAL

    STATS_WEEK_NO_TOTAL = """\
settimana        da:         a: #clienti #fatture incasso %incasso
2014:04   2014-01-20 2014-01-26        2        2  153.00  100.00%
"""
    STATS_WEEK_TOTAL = STATS_WEEK_NO_TOTAL + """\
TOTALE                                 2        2  153.00  100.00%
"""
    STATS_WEEK_DEFAULT = STATS_WEEK_TOTAL

    STATS_WEEKDAY_NO_TOTAL = """\
giorno           da:         a: #clienti #fatture incasso %incasso
Mercoledì 2014-01-22 2014-01-22        1        1  102.00   66.67%
Sabato    2014-01-25 2014-01-25        1        1   51.00   33.33%
"""
    STATS_WEEKDAY_TOTAL = STATS_WEEKDAY_NO_TOTAL + """\
TOTALE                                 2        2  153.00  100.00%
"""
    STATS_WEEKDAY_DEFAULT = STATS_WEEKDAY_TOTAL

    STATS_DAY_NO_TOTAL = """\
giorno            da:         a: #clienti #fatture incasso %incasso
2014-01-22 2014-01-22 2014-01-22        1        1  102.00   66.67%
2014-01-25 2014-01-25 2014-01-25        1        1   51.00   33.33%
"""
    STATS_DAY_TOTAL = STATS_DAY_NO_TOTAL + """\
TOTALE                                  2        2  153.00  100.00%
"""
    STATS_DAY_DEFAULT = STATS_DAY_TOTAL

    STATS_CLIENT_NO_TOTAL = """\
codice_fiscale          da:         a: nome                #fatture incasso %incasso
BNNBRC01G01H663S 2014-01-22 2014-01-22 Robert Bruce Banner        1  102.00   66.67%
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne                1   51.00   33.33%
"""
    STATS_CLIENT_TOTAL = STATS_CLIENT_NO_TOTAL + """\
TOTALE                                 --                         2  153.00  100.00%
"""
    STATS_CLIENT_DEFAULT = STATS_CLIENT_TOTAL

    STATS_CITY_NO_TOTAL = """\
città              da:         a: #clienti #fatture incasso %incasso
Gotham City 2014-01-25 2014-01-25        1        1   51.00   33.33%
Greenville  2014-01-22 2014-01-22        1        1  102.00   66.67%
"""
    STATS_CITY_TOTAL = STATS_CITY_NO_TOTAL + """\
TOTALE                                   2        2  153.00  100.00%
"""
    STATS_CITY_DEFAULT = STATS_CITY_TOTAL

    STATS_NONE_DEFAULT = STATS_MONTH_DEFAULT
    STATS_NONE_TOTAL = STATS_MONTH_TOTAL
    STATS_NONE_NO_TOTAL = STATS_MONTH_NO_TOTAL

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def _test_invoice_main_stats(self, stats_group, total, output):
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
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            args=['-d', db_filename.name, 'stats', '-S', '2014-01-10', '-E', '2014-01-27']
            if stats_group:
                args.append('-g{}'.format(stats_group))
            if total is not None:
                if total:
                    args.append('--total=on')
                else:
                    args.append('--total=off')
            invoice_main(
                printer=p,
                logger=self.logger,
                args=args,
            )
            self.assertEqual(p.string(), output)

    def test_invoice_main_stats_year(self):
        return self._test_invoice_main_stats('year', None, self.STATS_YEAR_DEFAULT)

    def test_invoice_main_stats_year_no_total(self):
        return self._test_invoice_main_stats('year', False, self.STATS_YEAR_NO_TOTAL)

    def test_invoice_main_stats_year_total(self):
        return self._test_invoice_main_stats('year', True, self.STATS_YEAR_TOTAL)

    def test_invoice_main_stats_month(self):
        return self._test_invoice_main_stats('month', None, self.STATS_MONTH_DEFAULT)

    def test_invoice_main_stats_month_no_total(self):
        return self._test_invoice_main_stats('month', False, self.STATS_MONTH_NO_TOTAL)

    def test_invoice_main_stats_month_total(self):
        return self._test_invoice_main_stats('month', True, self.STATS_MONTH_TOTAL)

    def test_invoice_main_stats_week(self):
        return self._test_invoice_main_stats('week', None, self.STATS_WEEK_DEFAULT)

    def test_invoice_main_stats_week_no_total(self):
        return self._test_invoice_main_stats('week', False, self.STATS_WEEK_NO_TOTAL)

    def test_invoice_main_stats_week_total(self):
        return self._test_invoice_main_stats('week', True, self.STATS_WEEK_TOTAL)

    def test_invoice_main_stats_weekday(self):
        return self._test_invoice_main_stats('weekday', None, self.STATS_WEEKDAY_DEFAULT)

    def test_invoice_main_stats_weekday_no_total(self):
        return self._test_invoice_main_stats('weekday', False, self.STATS_WEEKDAY_NO_TOTAL)

    def test_invoice_main_stats_weekday_total(self):
        return self._test_invoice_main_stats('weekday', True, self.STATS_WEEKDAY_TOTAL)

    def test_invoice_main_stats_day(self):
        return self._test_invoice_main_stats('day', None, self.STATS_DAY_DEFAULT)

    def test_invoice_main_stats_day_no_total(self):
        return self._test_invoice_main_stats('day', False, self.STATS_DAY_NO_TOTAL)

    def test_invoice_main_stats_day_total(self):
        return self._test_invoice_main_stats('day', True, self.STATS_DAY_TOTAL)

    def test_invoice_main_stats_name(self):
        return self._test_invoice_main_stats('client', None, self.STATS_CLIENT_DEFAULT)

    def test_invoice_main_stats_name_no_total(self):
        return self._test_invoice_main_stats('client', False, self.STATS_CLIENT_NO_TOTAL)

    def test_invoice_main_stats_name_total(self):
        return self._test_invoice_main_stats('client', True, self.STATS_CLIENT_TOTAL)

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', None, self.STATS_CITY_DEFAULT)

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', False, self.STATS_CITY_NO_TOTAL)

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', True, self.STATS_CITY_TOTAL)

    def test_invoice_main_stats_none(self):
        return self._test_invoice_main_stats(None, None, self.STATS_NONE_DEFAULT)

    def test_invoice_main_stats_none_no_total(self):
        return self._test_invoice_main_stats(None, False, self.STATS_NONE_NO_TOTAL)

    def test_invoice_main_stats_none_total(self):
        return self._test_invoice_main_stats(None, True, self.STATS_NONE_TOTAL)
