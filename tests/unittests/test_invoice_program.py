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
    'TestInvoiceProgram',
]

import datetime
import io
import os
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_program import InvoiceProgram
from invoice.database.db_types import Path

class Print(object):
    def __init__(self):
        self._s = io.StringIO()

    def __call__(self, *p_args, **n_args):
        return print(file=self._s, *p_args, **n_args)

    def string(self):
        return self._s.getvalue()

class TestInvoiceProgram(unittest.TestCase):
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()

    # invoice
    def test_InvoiceProgram(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
            )
            invoice_program.db_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            invoice_program.db_scan(
                warnings_mode=InvoiceCollection.WARNINGS_MODE_DEFAULT,
                raise_on_error=False,
                partial_update=None,
                remove_orphaned=None,
            )

            p = Print()
            invoice_program.db_list(
                field_names=('tax_code', 'year', 'number'),
                header=True,
                filters=(),
                print_function=p,
            )
            self.assertEqual(p.string(), """\
tax_code         year number
WNYBRC01G01H663Y 2014      1
PRKPRT01G01H663Y 2014      2
BNNBRC01G01H663Y 2014      3
WNYBRC01G01H663Y 2014      4
KNTCRK01G01H663Y 2014      5
""")
            p = Print()

            invoice_program.db_dump(
                filters=(),
                print_function=p,
            )
            p_cmp = """\
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
  total income:           76.00 [euro]
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
  total income:           152.00 [euro]
"""
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), p_cmp)
            p = Print()
            p_cmp = """\
year 2014:
  * number_of invoices:   5
  * number of clients:    4
    + client:             WNYBRC01G01H663Y (Bruce Wayne):
      number of invoices: 2
      total income:       102
      income percentage:  23.61%
      weeks:              1, 4

    + client:             PRKPRT01G01H663Y (Peter B. Parker):
      number of invoices: 1
      total income:       76
      income percentage:  17.59%
      weeks:              1

    + client:             BNNBRC01G01H663Y (Robert Bruce Banner):
      number of invoices: 1
      total income:       102
      income percentage:  23.61%
      weeks:              4

    + client:             KNTCRK01G01H663Y (Clark Kent):
      number of invoices: 1
      total income:       152
      income percentage:  35.19%
      weeks:              5

  * number of weeks:      3
    + week:               1 [2014-01-01 -> 2014-01-05]:
      number of invoices: 2
      total income:       127
      income percentage:  29.40%

    + week:               4 [2014-01-20 -> 2014-01-26]:
      number of invoices: 2
      total income:       153
      income percentage:  35.42%

    + week:               5 [2014-01-27 -> 2014-02-02]:
      number of invoices: 1
      total income:       152
      income percentage:  35.19%

"""
            invoice_program.db_report(print_function=p)
            self.assertEqual(p.string(), p_cmp)

