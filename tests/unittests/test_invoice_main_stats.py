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
    STATS_YEAR_NO_TOTAL_LONG = """\
anno        da:         a: clienti fatture incasso %incasso
2014 2014-01-10 2014-01-27       2       2  158.00  100.00%
"""
    STATS_YEAR_TOTAL_LONG = """\
anno          da:         a: clienti fatture incasso %incasso
2014   2014-01-10 2014-01-27       2       2  158.00  100.00%
TOTALE                             2       2  158.00  100.00%
"""
    STATS_YEAR_TOTAL_SHORT = """\
anno   clienti fatture incasso %incasso
2014         2       2  158.00  100.00%
TOTALE       2       2  158.00  100.00%
"""
    STATS_YEAR_TOTAL_FULL = """\
anno          da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
2014   2014-01-10 2014-01-27       2       2 ##########  158.00  100.00% ##########
TOTALE                             2       2 --          158.00  100.00% --        
"""
    STATS_YEAR_DEFAULT = STATS_YEAR_TOTAL_LONG

    STATS_MONTH_NO_TOTAL_LONG = """\
mese           da:         a: clienti fatture incasso %incasso
2014-01 2014-01-10 2014-01-27       2       2  158.00  100.00%
"""
    STATS_MONTH_TOTAL_LONG = STATS_MONTH_NO_TOTAL_LONG + """\
TOTALE                              2       2  158.00  100.00%
"""
    STATS_MONTH_TOTAL_SHORT = """\
mese    clienti fatture incasso %incasso
2014-01       2       2  158.00  100.00%
TOTALE        2       2  158.00  100.00%
"""
    STATS_MONTH_TOTAL_FULL = """\
mese           da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
2014-01 2014-01-10 2014-01-27       2       2 ##########  158.00  100.00% ##########
TOTALE                              2       2 --          158.00  100.00% --        
"""
    STATS_MONTH_DEFAULT = STATS_MONTH_TOTAL_LONG

    STATS_WEEK_NO_TOTAL_LONG = """\
settimana        da:         a: clienti fatture incasso %incasso
2014:04   2014-01-20 2014-01-26       2       2  158.00  100.00%
"""
    STATS_WEEK_TOTAL_LONG = STATS_WEEK_NO_TOTAL_LONG + """\
TOTALE                                2       2  158.00  100.00%
"""
    STATS_WEEK_TOTAL_SHORT = """\
settimana clienti fatture incasso %incasso
2014:04         2       2  158.00  100.00%
TOTALE          2       2  158.00  100.00%
"""
    STATS_WEEK_TOTAL_FULL = """\
settimana        da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
2014:04   2014-01-20 2014-01-26       2       2 ##########  158.00  100.00% ##########
TOTALE                                2       2 --          158.00  100.00% --        
"""
    STATS_WEEK_DEFAULT = STATS_WEEK_TOTAL_LONG

    STATS_WEEKDAY_NO_TOTAL_LONG = """\
giorno           da:         a: clienti fatture incasso %incasso
Mercoledì 2014-01-22 2014-01-22       1       1  107.00   67.72%
Sabato    2014-01-25 2014-01-25       1       1   51.00   32.28%
"""
    STATS_WEEKDAY_TOTAL_LONG = STATS_WEEKDAY_NO_TOTAL_LONG + """\
TOTALE                                2       2  158.00  100.00%
"""
    STATS_WEEKDAY_TOTAL_SHORT = """\
giorno    clienti fatture incasso %incasso
Mercoledì       1       1  107.00   67.72%
Sabato          1       1   51.00   32.28%
TOTALE          2       2  158.00  100.00%
"""
    STATS_WEEKDAY_TOTAL_FULL = """\
giorno           da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
Mercoledì 2014-01-22 2014-01-22       1       1 ##########  107.00   67.72% ##########
Sabato    2014-01-25 2014-01-25       1       1 ##########   51.00   32.28% #####     
TOTALE                                2       2 --          158.00  100.00% --        
"""
    STATS_WEEKDAY_DEFAULT = STATS_WEEKDAY_TOTAL_LONG

    STATS_DAY_NO_TOTAL_LONG = """\
giorno            da:         a: clienti fatture incasso %incasso
2014-01-22 2014-01-22 2014-01-22       1       1  107.00   67.72%
2014-01-25 2014-01-25 2014-01-25       1       1   51.00   32.28%
"""
    STATS_DAY_TOTAL_LONG = STATS_DAY_NO_TOTAL_LONG + """\
TOTALE                                 2       2  158.00  100.00%
"""
    STATS_DAY_TOTAL_SHORT = """\
giorno     clienti fatture incasso %incasso
2014-01-22       1       1  107.00   67.72%
2014-01-25       1       1   51.00   32.28%
TOTALE           2       2  158.00  100.00%
"""
    STATS_DAY_TOTAL_FULL = """\
giorno            da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
2014-01-22 2014-01-22 2014-01-22       1       1 ##########  107.00   67.72% ##########
2014-01-25 2014-01-25 2014-01-25       1       1 ##########   51.00   32.28% #####     
TOTALE                                 2       2 --          158.00  100.00% --        
"""
    STATS_DAY_DEFAULT = STATS_DAY_TOTAL_LONG

    STATS_CLIENT_NO_TOTAL_LONG = """\
codice_fiscale          da:         a: nome                cont. fatture incasso %incasso
BNNBRC01G01H663S 2014-01-22 2014-01-22 Robert Bruce Banner [---]       1  107.00   67.72%
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne         <---]       1   51.00   32.28%
"""
    STATS_CLIENT_TOTAL_LONG = STATS_CLIENT_NO_TOTAL_LONG + """\
TOTALE                                 --                  --          2  158.00  100.00%
"""
    STATS_CLIENT_TOTAL_SHORT = """\
codice_fiscale   nome                cont. fatture incasso %incasso
BNNBRC01G01H663S Robert Bruce Banner [---]       1  107.00   67.72%
WNYBRC01G01H663S Bruce Wayne         <---]       1   51.00   32.28%
TOTALE           --                  --          2  158.00  100.00%
"""
    STATS_CLIENT_TOTAL_FULL = """\
codice_fiscale          da:         a: nome                cont. fatture h(fatture) incasso %incasso h(incasso)
BNNBRC01G01H663S 2014-01-22 2014-01-22 Robert Bruce Banner [---]       1 ##########  107.00   67.72% ##########
WNYBRC01G01H663S 2014-01-25 2014-01-25 Bruce Wayne         <---]       1 ##########   51.00   32.28% #####     
TOTALE                                 --                  --          2 --          158.00  100.00% --        
"""
    STATS_CLIENT_DEFAULT = STATS_CLIENT_TOTAL_LONG

    STATS_CITY_NO_TOTAL_LONG = """\
città              da:         a: clienti fatture incasso %incasso
Gotham City 2014-01-25 2014-01-25       1       1   51.00   32.28%
Greenville  2014-01-22 2014-01-22       1       1  107.00   67.72%
"""
    STATS_CITY_TOTAL_LONG = STATS_CITY_NO_TOTAL_LONG + """\
TOTALE                                  2       2  158.00  100.00%
"""
    STATS_CITY_TOTAL_SHORT = """\
città       clienti fatture incasso %incasso
Gotham City       1       1   51.00   32.28%
Greenville        1       1  107.00   67.72%
TOTALE            2       2  158.00  100.00%
"""
    STATS_CITY_TOTAL_FULL = """\
città              da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
Gotham City 2014-01-25 2014-01-25       1       1 ##########   51.00   32.28% #####     
Greenville  2014-01-22 2014-01-22       1       1 ##########  107.00   67.72% ##########
TOTALE                                  2       2 --          158.00  100.00% --        
"""
    STATS_CITY_DEFAULT = STATS_CITY_TOTAL_LONG

    STATS_SERVICE_NO_TOTAL_LONG = """\
prestazione                                    da:         a: clienti fatture incasso %incasso
Group therapy for depressed superheroes 2014-01-25 2014-01-25       1       1   51.00   32.28%
Therapy for rage control                2014-01-22 2014-01-22       1       1  107.00   67.72%
"""
    STATS_SERVICE_TOTAL_LONG = STATS_SERVICE_NO_TOTAL_LONG + """\
TOTALE                                                              2       2  158.00  100.00%
"""
    STATS_SERVICE_TOTAL_SHORT = """\
prestazione                             clienti fatture incasso %incasso
Group therapy for depressed superheroes       1       1   51.00   32.28%
Therapy for rage control                      1       1  107.00   67.72%
TOTALE                                        2       2  158.00  100.00%
"""
    STATS_SERVICE_TOTAL_FULL = """\
prestazione                                    da:         a: clienti fatture h(fatture) incasso %incasso h(incasso)
Group therapy for depressed superheroes 2014-01-25 2014-01-25       1       1 ##########   51.00   32.28% #####     
Therapy for rage control                2014-01-22 2014-01-22       1       1 ##########  107.00   67.72% ##########
TOTALE                                                              2       2 --          158.00  100.00% --        
"""
    STATS_SERVICE_DEFAULT = STATS_SERVICE_TOTAL_LONG

    STATS_TASK_NO_TOTAL_LONG = """\
codice_fiscale   nome                prestazione                                    da:         a: fatture incasso %incasso
BNNBRC01G01H663S Robert Bruce Banner Therapy for rage control                2014-01-22 2014-01-22       1  107.00   67.72%
WNYBRC01G01H663S Bruce Wayne         Group therapy for depressed superheroes 2014-01-25 2014-01-25       1   51.00   32.28%
"""
    STATS_TASK_TOTAL_LONG = STATS_TASK_NO_TOTAL_LONG + """\
TOTALE                                                                                                   2  158.00  100.00%
"""
    STATS_TASK_TOTAL_SHORT = """\
codice_fiscale   nome                prestazione                             fatture incasso %incasso
BNNBRC01G01H663S Robert Bruce Banner Therapy for rage control                      1  107.00   67.72%
WNYBRC01G01H663S Bruce Wayne         Group therapy for depressed superheroes       1   51.00   32.28%
TOTALE                                                                             2  158.00  100.00%
"""
    STATS_TASK_TOTAL_FULL = """\
codice_fiscale   nome                prestazione                                    da:         a: fatture h(fatture) incasso %incasso h(incasso)
BNNBRC01G01H663S Robert Bruce Banner Therapy for rage control                2014-01-22 2014-01-22       1 ##########  107.00   67.72% ##########
WNYBRC01G01H663S Bruce Wayne         Group therapy for depressed superheroes 2014-01-25 2014-01-25       1 ##########   51.00   32.28% #####     
TOTALE                                                                                                   2 --          158.00  100.00% --        
"""
    STATS_TASK_DEFAULT = STATS_TASK_TOTAL_LONG

    STATS_NONE_DEFAULT = STATS_MONTH_DEFAULT
    STATS_NONE_TOTAL_LONG = STATS_MONTH_TOTAL_LONG
    STATS_NONE_NO_TOTAL_LONG = STATS_MONTH_NO_TOTAL_LONG
    STATS_NONE_TOTAL_SHORT = STATS_MONTH_TOTAL_SHORT
    STATS_NONE_TOTAL_LONG = STATS_MONTH_TOTAL_LONG
    STATS_NONE_TOTAL_FULL = STATS_MONTH_TOTAL_FULL

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def _test_invoice_main_stats(self, stats_group, total, output, mode_flag=None):
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
                args=['scan', '-R', rc_dir, '--progressbar=off'],
            )
            self.assertEqual(p.string(), '')

            args=['stats', '-R', rc_dir, '-S', '2014-01-10', '-E', '2014-01-27']
            if stats_group:
                args.append('-g{}'.format(stats_group))
            if total is not None:
                if total:
                    args.append('--total=on')
                else:
                    args.append('--total=off')
            if mode_flag:
                args.append(mode_flag)
            invoice_main(
                printer=p,
                logger=self.logger,
                args=args,
            )
            print(p.string())
            self.assertEqual(p.string(), output)

    def test_invoice_main_stats_service(self):
        return self._test_invoice_main_stats('service', None, self.STATS_SERVICE_DEFAULT)

    def test_invoice_main_stats_service_no_total(self):
        return self._test_invoice_main_stats('service', False, self.STATS_SERVICE_NO_TOTAL_LONG)

    def test_invoice_main_stats_service_total(self):
        return self._test_invoice_main_stats('service', True, self.STATS_SERVICE_TOTAL_LONG)

    def test_invoice_main_stats_service_total_short(self):
        return self._test_invoice_main_stats('service', True, self.STATS_SERVICE_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_service_total_long(self):
        return self._test_invoice_main_stats('service', True, self.STATS_SERVICE_TOTAL_LONG, '-l')

    def test_invoice_main_stats_service_total_full(self):
        return self._test_invoice_main_stats('service', True, self.STATS_SERVICE_TOTAL_FULL, '-f')

    def test_invoice_main_stats_task(self):
        return self._test_invoice_main_stats('task', None, self.STATS_TASK_DEFAULT)

    def test_invoice_main_stats_task_no_total(self):
        return self._test_invoice_main_stats('task', False, self.STATS_TASK_NO_TOTAL_LONG)

    def test_invoice_main_stats_task_total(self):
        return self._test_invoice_main_stats('task', True, self.STATS_TASK_TOTAL_LONG)

    def test_invoice_main_stats_task_total_short(self):
        return self._test_invoice_main_stats('task', True, self.STATS_TASK_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_task_total_long(self):
        return self._test_invoice_main_stats('task', True, self.STATS_TASK_TOTAL_LONG, '-l')

    def test_invoice_main_stats_task_total_full(self):
        return self._test_invoice_main_stats('task', True, self.STATS_TASK_TOTAL_FULL, '-f')

    def test_invoice_main_stats_year(self):
        return self._test_invoice_main_stats('year', None, self.STATS_YEAR_DEFAULT)

    def test_invoice_main_stats_year_no_total(self):
        return self._test_invoice_main_stats('year', False, self.STATS_YEAR_NO_TOTAL_LONG)

    def test_invoice_main_stats_year_total(self):
        return self._test_invoice_main_stats('year', True, self.STATS_YEAR_TOTAL_LONG)

    def test_invoice_main_stats_year_total_short(self):
        return self._test_invoice_main_stats('year', True, self.STATS_YEAR_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_year_total_long(self):
        return self._test_invoice_main_stats('year', True, self.STATS_YEAR_TOTAL_LONG, '-l')

    def test_invoice_main_stats_year_total_full(self):
        return self._test_invoice_main_stats('year', True, self.STATS_YEAR_TOTAL_FULL, '-f')

    def test_invoice_main_stats_month(self):
        return self._test_invoice_main_stats('month', None, self.STATS_MONTH_DEFAULT)

    def test_invoice_main_stats_month_no_total(self):
        return self._test_invoice_main_stats('month', False, self.STATS_MONTH_NO_TOTAL_LONG)

    def test_invoice_main_stats_month_total(self):
        return self._test_invoice_main_stats('month', True, self.STATS_MONTH_TOTAL_LONG)

    def test_invoice_main_stats_month_total_short(self):
        return self._test_invoice_main_stats('month', True, self.STATS_MONTH_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_month_total_long(self):
        return self._test_invoice_main_stats('month', True, self.STATS_MONTH_TOTAL_LONG, '-l')

    def test_invoice_main_stats_month_total_full(self):
        return self._test_invoice_main_stats('month', True, self.STATS_MONTH_TOTAL_FULL, '-f')

    def test_invoice_main_stats_week(self):
        return self._test_invoice_main_stats('week', None, self.STATS_WEEK_DEFAULT)

    def test_invoice_main_stats_week_no_total(self):
        return self._test_invoice_main_stats('week', False, self.STATS_WEEK_NO_TOTAL_LONG)

    def test_invoice_main_stats_week_total(self):
        return self._test_invoice_main_stats('week', True, self.STATS_WEEK_TOTAL_LONG)

    def test_invoice_main_stats_week_total_short(self):
        return self._test_invoice_main_stats('week', True, self.STATS_WEEK_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_week_total_long(self):
        return self._test_invoice_main_stats('week', True, self.STATS_WEEK_TOTAL_LONG, '-l')

    def test_invoice_main_stats_week_total_full(self):
        return self._test_invoice_main_stats('week', True, self.STATS_WEEK_TOTAL_FULL, '-f')

    def test_invoice_main_stats_weekday(self):
        return self._test_invoice_main_stats('weekday', None, self.STATS_WEEKDAY_DEFAULT)

    def test_invoice_main_stats_weekday_no_total(self):
        return self._test_invoice_main_stats('weekday', False, self.STATS_WEEKDAY_NO_TOTAL_LONG)

    def test_invoice_main_stats_weekday_total(self):
        return self._test_invoice_main_stats('weekday', True, self.STATS_WEEKDAY_TOTAL_LONG)

    def test_invoice_main_stats_weekday_total_short(self):
        return self._test_invoice_main_stats('weekday', True, self.STATS_WEEKDAY_TOTAL_SHORT, '--short')

    def test_invoice_main_stats_weekday_total_long(self):
        return self._test_invoice_main_stats('weekday', True, self.STATS_WEEKDAY_TOTAL_LONG, '--long')

    def test_invoice_main_stats_weekday_total_full(self):
        return self._test_invoice_main_stats('weekday', True, self.STATS_WEEKDAY_TOTAL_FULL, '--full')

    def test_invoice_main_stats_day(self):
        return self._test_invoice_main_stats('day', None, self.STATS_DAY_DEFAULT)

    def test_invoice_main_stats_day_no_total(self):
        return self._test_invoice_main_stats('day', False, self.STATS_DAY_NO_TOTAL_LONG)

    def test_invoice_main_stats_day_total(self):
        return self._test_invoice_main_stats('day', True, self.STATS_DAY_TOTAL_LONG)

    def test_invoice_main_stats_day_total_short(self):
        return self._test_invoice_main_stats('day', True, self.STATS_DAY_TOTAL_SHORT, '--short')

    def test_invoice_main_stats_day_total_long(self):
        return self._test_invoice_main_stats('day', True, self.STATS_DAY_TOTAL_LONG, '--long')

    def test_invoice_main_stats_day_total_full(self):
        return self._test_invoice_main_stats('day', True, self.STATS_DAY_TOTAL_FULL, '--full')

    def test_invoice_main_stats_client(self):
        return self._test_invoice_main_stats('client', None, self.STATS_CLIENT_DEFAULT)

    def test_invoice_main_stats_client_no_total(self):
        return self._test_invoice_main_stats('client', False, self.STATS_CLIENT_NO_TOTAL_LONG)

    def test_invoice_main_stats_client_total(self):
        return self._test_invoice_main_stats('client', True, self.STATS_CLIENT_TOTAL_LONG)

    def test_invoice_main_stats_client_total_short(self):
        return self._test_invoice_main_stats('client', True, self.STATS_CLIENT_TOTAL_SHORT, '--short')

    def test_invoice_main_stats_client_total_long(self):
        return self._test_invoice_main_stats('client', True, self.STATS_CLIENT_TOTAL_LONG, '--long')

    def test_invoice_main_stats_client_total_full(self):
        return self._test_invoice_main_stats('client', True, self.STATS_CLIENT_TOTAL_FULL, '--full')

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', None, self.STATS_CITY_DEFAULT)

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', False, self.STATS_CITY_NO_TOTAL_LONG)

    def test_invoice_main_stats_city(self):
        return self._test_invoice_main_stats('city', True, self.STATS_CITY_TOTAL_LONG)

    def test_invoice_main_stats_city_short(self):
        return self._test_invoice_main_stats('city', True, self.STATS_CITY_TOTAL_SHORT, '--short')

    def test_invoice_main_stats_city_long(self):
        return self._test_invoice_main_stats('city', True, self.STATS_CITY_TOTAL_LONG, '--long')

    def test_invoice_main_stats_city_full(self):
        return self._test_invoice_main_stats('city', True, self.STATS_CITY_TOTAL_FULL, '--full')

    def test_invoice_main_stats_none(self):
        return self._test_invoice_main_stats(None, None, self.STATS_NONE_DEFAULT)

    def test_invoice_main_stats_none_no_total(self):
        return self._test_invoice_main_stats(None, False, self.STATS_NONE_NO_TOTAL_LONG)

    def test_invoice_main_stats_none_total(self):
        return self._test_invoice_main_stats(None, True, self.STATS_NONE_TOTAL_LONG)

    def test_invoice_main_stats_none_total_short(self):
        return self._test_invoice_main_stats(None, True, self.STATS_NONE_TOTAL_SHORT, '-s')

    def test_invoice_main_stats_none_total_long(self):
        return self._test_invoice_main_stats(None, True, self.STATS_NONE_TOTAL_LONG, '-l')

    def test_invoice_main_stats_none_total_full(self):
        return self._test_invoice_main_stats(None, True, self.STATS_NONE_TOTAL_FULL, '-f')
