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
    'TestMain',
]

import datetime
import io
import os
import tempfile
import unittest

from invoice.log import get_default_logger, get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_main import invoice_main
from invoice.database.db_types import Path

class Print(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._s = io.StringIO()

    def __call__(self, *p_args, **n_args):
        return print(file=self._s, *p_args, **n_args)

    def string(self):
        return self._s.getvalue()

class Test_main(unittest.TestCase):
    DUMP_OUTPUT = """\
invoice:                  '<DIRNAME>/2014_001_bruce_wayne.doc'
  year/number:            2014/1
  city/date:              Gotham City/2014-01-03
  name:                   Bruce Wayne
  tax code:               WNYBRC01G01H663Y
  total income:           51.00 [euro]
invoice:                  '<DIRNAME>/2014_002_peter_parker.doc'
  year/number:            2014/2
  city/date:              New York City/2014-01-03
  name:                   Peter B. Parker
  tax code:               PRKPRT01G01H663Y
  total income:           76.50 [euro]
invoice:                  '<DIRNAME>/2014_003_bruce_banner.doc'
  year/number:            2014/3
  city/date:              Greenville/2014-01-22
  name:                   Robert Bruce Banner
  tax code:               BNNBRC01G01H663Y
  total income:           102.00 [euro]
invoice:                  '<DIRNAME>/2014_004_bruce_wayne.doc'
  year/number:            2014/4
  city/date:              Gotham City/2014-01-25
  name:                   Bruce Wayne
  tax code:               WNYBRC01G01H663Y
  total income:           51.00 [euro]
invoice:                  '<DIRNAME>/2014_005_clark_kent.doc'
  year/number:            2014/5
  city/date:              Smallville/2014-01-29
  name:                   Clark Kent
  tax code:               KNTCRK01G01H663Y
  total income:           152.50 [euro]
"""
    REPORT_OUTPUT = """\
year 2014:
  * number_of invoices:   5
  * number of clients:    4
    + client:             WNYBRC01G01H663Y (Bruce Wayne):
      number of invoices: 2
      total income:       102.0
      income percentage:  23.56%
      weeks:              1, 4

    + client:             PRKPRT01G01H663Y (Peter B. Parker):
      number of invoices: 1
      total income:       76.5
      income percentage:  17.67%
      weeks:              1

    + client:             BNNBRC01G01H663Y (Robert Bruce Banner):
      number of invoices: 1
      total income:       102.0
      income percentage:  23.56%
      weeks:              4

    + client:             KNTCRK01G01H663Y (Clark Kent):
      number of invoices: 1
      total income:       152.5
      income percentage:  35.22%
      weeks:              5

  * number of weeks:      3
    + week:               1 [2014-01-01 -> 2014-01-05]:
      number of invoices: 2
      total income:       127.5
      income percentage:  29.45%

    + week:               4 [2014-01-20 -> 2014-01-26]:
      number of invoices: 2
      total income:       153.0
      income percentage:  35.33%

    + week:               5 [2014-01-27 -> 2014-02-02]:
      number of invoices: 1
      total income:       152.5
      income percentage:  35.22%

"""

    CONFIG_SHOW_PARTIAL_UPDATE_ON = """\
patterns:
  + Pattern(pattern='<DIRNAME>/*.doc')

configuration:
  + remove_orphaned      = False
  + partial_update       = True
"""
    CONFIG_SHOW_PARTIAL_UPDATE_OFF = """\
patterns:
  + Pattern(pattern='<DIRNAME>/*.doc')

configuration:
  + remove_orphaned      = False
  + partial_update       = False
"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    # invoice
    def test_Main(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan', '-vvv'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number'],
            )
            self.assertEqual(p.string(), """\
tax_code         year number
WNYBRC01G01H663Y 2014      1
PRKPRT01G01H663Y 2014      2
BNNBRC01G01H663Y 2014      3
WNYBRC01G01H663Y 2014      4
KNTCRK01G01H663Y 2014      5
""")

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'dump'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'report'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'config', '--partial-update=on', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'config', '--partial-update=off', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)

    def test_MainLegacy(self):
            p = Print()

            pattern = os.path.join(self.dirname, '*.doc')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['legacy', pattern, '-l']
            )
            
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['legacy', pattern, '-r']
            )
            
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.REPORT_OUTPUT)
