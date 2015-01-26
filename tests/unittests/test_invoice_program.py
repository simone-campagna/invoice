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
from invoice.error import InvoiceDuplicatedNumberError
from invoice.invoice_program import InvoiceProgram
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

class TestInvoiceProgram(unittest.TestCase):
    DUMP_OUTPUT = """\
fattura:                   '<DIRNAME>/2014_001_bruce_wayne.doc'
  anno/numero:             2014/1
  città/data:              Gotham City/2014-01-03
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663Y
  importo:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_002_peter_parker.doc'
  anno/numero:             2014/2
  città/data:              New York City/2014-01-03
  nome:                    Peter B. Parker
  codice fiscale:          PRKPRT01G01H663Y
  importo:                 76.50 [euro]
fattura:                   '<DIRNAME>/2014_003_bruce_banner.doc'
  anno/numero:             2014/3
  città/data:              Greenville/2014-01-22
  nome:                    Robert Bruce Banner
  codice fiscale:          BNNBRC01G01H663Y
  importo:                 102.00 [euro]
fattura:                   '<DIRNAME>/2014_004_bruce_wayne.doc'
  anno/numero:             2014/4
  città/data:              Gotham City/2014-01-25
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663Y
  importo:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_005_clark_kent.doc'
  anno/numero:             2014/5
  città/data:              Smallville/2014-01-29
  nome:                    Clark Kent
  codice fiscale:          KNTCRK01G01H663Y
  importo:                 152.50 [euro]
"""

    REPORT_OUTPUT = """\
anno                       2014
  * numero di fatture:     5
  * numero di clienti:     4
    + cliente:             WNYBRC01G01H663Y (Bruce Wayne):
      numero di fatture:   2
      incasso totale:      102.0
      incasso percentuale: 23.56%
      settimane:           1, 4

    + cliente:             PRKPRT01G01H663Y (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      76.5
      incasso percentuale: 17.67%
      settimane:           1

    + cliente:             BNNBRC01G01H663Y (Robert Bruce Banner):
      numero di fatture:   1
      incasso totale:      102.0
      incasso percentuale: 23.56%
      settimane:           4

    + cliente:             KNTCRK01G01H663Y (Clark Kent):
      numero di fatture:   1
      incasso totale:      152.5
      incasso percentuale: 35.22%
      settimane:           5

  * numero di settimane:   3
    + settimana:           1 [2014-01-01 -> 2014-01-05]:
      numero di fatture:   2
      incasso totale:      127.5
      incasso percentuale: 29.45%

    + settimana:           4 [2014-01-20 -> 2014-01-26]:
      numero di fatture:   2
      incasso totale:      153.0
      incasso percentuale: 35.33%

    + settimana:           5 [2014-01-27 -> 2014-02-02]:
      numero di fatture:   1
      incasso totale:      152.5
      incasso percentuale: 35.22%

"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()

    # invoice
    def test_InvoiceProgram(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
            invoice_program.db_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            invoice_program.db_scan(
                warnings_mode=InvoiceProgram.WARNINGS_MODE_DEFAULT,
                raise_on_error=False,
                partial_update=None,
                remove_orphaned=None,
            )

            invoice_program.db_list(
                field_names=('tax_code', 'year', 'number'),
                header=True,
                filters=(),
            )

            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663Y 2014      1
PRKPRT01G01H663Y 2014      2
BNNBRC01G01H663Y 2014      3
WNYBRC01G01H663Y 2014      4
KNTCRK01G01H663Y 2014      5
""")
            p.reset()

            invoice_program.db_dump(
                filters=(),
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)
            p.reset()
            invoice_program.db_report()
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

    # invoice
    def test_InvoiceProgramError(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()

            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )

            p.reset()
            invoice_program.db_init(
                patterns=[os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_duplicated_number/*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            p.reset()
            with self.assertRaises(InvoiceDuplicatedNumberError):
                invoice_program.db_scan(
                    warnings_mode=InvoiceProgram.WARNINGS_MODE_DEFAULT,
                    raise_on_error=True,
                    partial_update=None,
                    remove_orphaned=None,
                )


