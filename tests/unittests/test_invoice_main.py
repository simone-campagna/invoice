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
    'Test_invoice_main',
]

import datetime
import glob
import os
import sys
import tempfile
import unittest

from invoice import conf
from invoice.log import get_null_logger
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice_main import invoice_main
from invoice.invoice_db import InvoiceDb
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter

class Test_invoice_main(unittest.TestCase):
    DUMP_OUTPUT = """\
fattura:                   '<DIRNAME>/2014_001_bruce_wayne.doc'
  anno/numero:             2014/1
  città/data:              Gotham City/2014-01-03
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663S
  incasso:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_002_peter_parker.doc'
  anno/numero:             2014/2
  città/data:              New York City/2014-01-03
  nome:                    Peter B. Parker
  codice fiscale:          PRKPRT01G01H663M
  incasso:                 76.50 [euro]
fattura:                   '<DIRNAME>/2014_003_bruce_banner.doc'
  anno/numero:             2014/3
  città/data:              Greenville/2014-01-22
  nome:                    Robert Bruce Banner
  codice fiscale:          BNNBRC01G01H663S
  incasso:                 102.00 [euro]
fattura:                   '<DIRNAME>/2014_004_bruce_wayne.doc'
  anno/numero:             2014/4
  città/data:              Gotham City/2014-01-25
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663S
  incasso:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_005_clark_kent.doc'
  anno/numero:             2014/5
  città/data:              Smallville/2014-01-29
  nome:                    Clark Kent
  codice fiscale:          KNTCRK01G01H663X
  incasso:                 152.50 [euro]
"""
    REPORT_OUTPUT = """\
anno                       2014
  * incasso totale:        433.00
  * numero di fatture:     5
  * numero di clienti:     4
    + cliente:             WNYBRC01G01H663S (Bruce Wayne):
      numero di fatture:   2
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           1, 4

    + cliente:             PRKPRT01G01H663M (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      76.50
      incasso percentuale: 17.67%
      settimane:           1

    + cliente:             BNNBRC01G01H663S (Robert Bruce Banner):
      numero di fatture:   1
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           4

    + cliente:             KNTCRK01G01H663X (Clark Kent):
      numero di fatture:   1
      incasso totale:      152.50
      incasso percentuale: 35.22%
      settimane:           5

  * numero di settimane:   3
    + settimana:           1 [2014-01-01 -> 2014-01-05]:
      numero di fatture:   2
      giorni:              2014-01-03 VE[2]
      incasso totale:      127.50
      incasso percentuale: 29.45%

    + settimana:           4 [2014-01-20 -> 2014-01-26]:
      numero di fatture:   2
      giorni:              2014-01-22 ME[1], 2014-01-25 SA[1]
      incasso totale:      153.00
      incasso percentuale: 35.33%

    + settimana:           5 [2014-01-27 -> 2014-02-02]:
      numero di fatture:   1
      giorni:              2014-01-29 ME[1]
      incasso totale:      152.50
      incasso percentuale: 35.22%

"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main(self):
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

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'dump'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'report', '-y', '2014'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'report', '-y', '2014,2015'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--filter', 'number % 2 == 0', '--filter=tax_code.startswith("P")'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
PRKPRT01G01H663M 2014      2
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'validate'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'clear'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--header=off', '--filter', 'città == Rome'], # InvoiceSyntaxError
            )
            self.assertEqual(p.string(), '')

    def test_invoice_main_list(self):
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

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'date, city,tax_code,year,number', '--filter', 'città != "Gotham City"', '-S', '2014-01-10', '-E', '2014-01-27'],
            )
            self.assertEqual(p.string(), """\
data       città      codice_fiscale   anno numero
2014-01-22 Greenville BNNBRC01G01H663S 2014      3
""")

#WNYBRC01G01H663S 2014      1
#PRKPRT01G01H663M 2014      2
#BNNBRC01G01H663S 2014      3
#WNYBRC01G01H663S 2014      4
#KNTCRK01G01H663X 2014      5
#
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--client', 'WNYBRC01G01H663S'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663S 2014      1
WNYBRC01G01H663S 2014      4
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--client', 'PRKPRT01G01H663M,WNYBRC01G01H663S'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663S 2014      1
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      4
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--client', 'PRKPRT01G01H663M,WNYBRC01G01H663S',
                      '--order', 'tax_code' ],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      1
WNYBRC01G01H663S 2014      4
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--order', 'tax_code'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      5
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      1
WNYBRC01G01H663S 2014      4
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--order', 'tax_code,!date'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      5
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      4
WNYBRC01G01H663S 2014      1
""")

            with tempfile.NamedTemporaryFile() as o_file:
                p.reset()
                invoice_main(
                    printer=p,
                    logger=self.logger,
                    args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--order', 'tax_code,!date', '--output', o_file.name],
                )
                self.assertEqual(p.string(), "")
                o_file.flush()
                with open(o_file.name, 'r') as f_in:
                    o_content = f_in.read()
                self.assertEqual(o_content, """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      5
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      4
WNYBRC01G01H663S 2014      1
""")

                idx = 0
                while True:
                    o_filename_template = o_file.name + '.' + str(idx) + '.{mode}'
                    o_filename = o_filename_template.format(mode=conf.TABLE_MODE_XLSX)
                    if not os.path.exists(o_filename):
                        break

                p.reset()
                invoice_main(
                    printer=p,
                    logger=self.logger,
                    args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--order', 'tax_code,!date', '--output', o_filename_template, '--table-mode', conf.TABLE_MODE_XLSX],
                )
                try:
                    self.assertEqual(p.string(), "")
                    self.assertTrue(os.path.exists(o_filename))
                finally:
                    os.remove(o_filename)

    def test_invoice_main_dry_run(self):
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
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), "")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan', '--dry-run'],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), "")

    def _test_invoice_main_global_options(self, *global_options):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = StringPrinter()

            args = list(global_options) + ['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc')]
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=args,
            )

    def test_invoice_main_v(self):
        self._test_invoice_main_global_options('-v')

    def test_invoice_main_vv(self):
        self._test_invoice_main_global_options('-vv')

    def test_invoice_main_vvv(self):
        self._test_invoice_main_global_options('-vvv')

    def test_invoice_main_legacy(self):
        p = StringPrinter()

        pattern = os.path.join(self.dirname, '*.doc')

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=['legacy', pattern, '-l']
        )
        
        self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=['legacy', pattern, '-r']
        )
        
        self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.REPORT_OUTPUT)

    def test_invoice_main_legacy_err(self):
        p = StringPrinter()

        pattern0 = os.path.join(self.dirname, '*.doc')
        pattern1 = os.path.join(self.dirname, 'error_duplicated_line', '*.doc')

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=['legacy', pattern0, pattern1, '-l', '-eraise']
        )
            

    def test_invoice_main_help(self):
        p = StringPrinter()

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help"]
        )

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "scan"]
        )

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "unknown_command"]
        )

    def test_invoice_main_help(self):
        p = StringPrinter()

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "errors"]
        )
        self.assertEqual(p.string(), """\
[001] la fattura contiene linee duplicate
[002] il DOC file è assente
[003] la numerazione delle fatture è inconsistente
[004] la numerazione contiene dei duplicati
[005] la numerazione contiene numeri non consecutivi
[006] la valuta non è supportata
[007] più nomi sono associati allo stesso codice fiscale
[008] più codici fiscali sono associati allo stesso nome
[009] sono state generate più fatture per lo stesso cliente nello stesso giorno
[010] il codice fiscale non è corretto
[011] il codice fiscale è malformato
[012] un validatore fornisce errore
[013] un campo obbligatorio non è definito
[014] la data non è corretta
[015] l'anno non è corretto
""")

    def test_invoice_main_missing_subcommand(self):
        p = StringPrinter()

        p.reset()
        if sys.version_info.minor >= 3:
            # since python 3.3, missing subcommand does not raise
            invoice_main(
                printer=p,
                logger=self.logger,
                args=[],
            )
        else:
            # before python 3.2, missing subcommand raises SystemExit
            with self.assertRaises(SystemExit) as cm:
                invoice_main(
                    printer=p,
                    logger=self.logger,
                    args=[],
                )
            self.assertEqual(cm.exception.code, 2)
