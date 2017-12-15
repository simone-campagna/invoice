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
  incasso:                 107.00 [euro]
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
  incasso:                 155.00 [euro]
fattura:                   '<DIRNAME>/2014_006_clark_kent.doc'
  anno/numero:             2014/6
  città/data:              Smallville/2014-02-28
  nome:                    Clark Kent
  codice fiscale:          KNTCRK01G01H663X
  incasso:                 246.66 [euro]
"""
    REPORT_OUTPUT = """\
anno                       2014
  * incasso totale:        687.16
  * numero di fatture:     6
  * numero di clienti:     4
    + cliente:             WNYBRC01G01H663S (Bruce Wayne):
      numero di fatture:   2
      incasso totale:      102.00
      incasso percentuale: 14.84%
      settimane:           1, 4

    + cliente:             PRKPRT01G01H663M (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      76.50
      incasso percentuale: 11.13%
      settimane:           1

    + cliente:             BNNBRC01G01H663S (Robert Bruce Banner):
      numero di fatture:   1
      incasso totale:      107.00
      incasso percentuale: 15.57%
      settimane:           4

    + cliente:             KNTCRK01G01H663X (Clark Kent):
      numero di fatture:   2
      incasso totale:      401.66
      incasso percentuale: 58.45%
      settimane:           5, 9

  * numero di settimane:   4
    + settimana:           1 [2014-01-01 -> 2014-01-05]:
      numero di fatture:   2
      giorni:              2014-01-03 VE[2]
      incasso totale:      127.50
      incasso percentuale: 18.55%

    + settimana:           4 [2014-01-20 -> 2014-01-26]:
      numero di fatture:   2
      giorni:              2014-01-22 ME[1], 2014-01-25 SA[1]
      incasso totale:      158.00
      incasso percentuale: 22.99%

    + settimana:           5 [2014-01-27 -> 2014-02-02]:
      numero di fatture:   1
      giorni:              2014-01-29 ME[1]
      incasso totale:      155.00
      incasso percentuale: 22.56%

    + settimana:           9 [2014-02-24 -> 2014-03-02]:
      numero di fatture:   1
      giorni:              2014-02-28 VE[1]
      incasso totale:      246.66
      incasso percentuale: 35.90%

"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main(self):
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

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-R', rc_dir, '--progressbar=off'],
            )
            self.assertEqual(p.string(), '')

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
                args=['dump', '-R', rc_dir],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['report', '-R', rc_dir, '-y', '2014'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['report', '-R', rc_dir, '-y', '2014,2015'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--filter', 'number % 2 == 0', '--filter=tax_code.startswith("P")'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
PRKPRT01G01H663M 2014      2
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['validate', '-R', rc_dir],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['clear', '-R', rc_dir],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--header=off', '--filter', 'città == Rome'], # InvoiceSyntaxError
            )
            self.assertEqual(p.string(), '')

    def _test_invoice_main_summary(self, table_mode, pdata):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            if pdata:
                with open(os.path.join(rc_dir, "info.config"), "w") as f_out:
                    f_out.write("""
[general]
summary_prologue = test line 0
    test line 1
    test line 2
summary_epilogue = test line 3
    test line 4
""")
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

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['summary', '-R', rc_dir, '--year', '2014'],
            )
            if table_mode == conf.TABLE_MODE_TEXT:
                print(p.string())
                self.assertEqual(p.string(), """\
=== Gennaio ===
N.DOC. DATA       CODICE FISCALE   NOME                COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
     1 2014-01-03 WNYBRC01G01H663S Bruce Wayne             50.0      0.0    1.0           51.0     0.0                0.0   0.0   51.0
     2 2014-01-03 PRKPRT01G01H663M Peter B. Parker         75.0      0.0    1.5           76.5     0.0                0.0   0.0   76.5
     3 2014-01-22 BNNBRC01G01H663S Robert Bruce Banner    100.0      0.0    2.0          102.0     0.0                0.0   5.0  107.0
     4 2014-01-25 WNYBRC01G01H663S Bruce Wayne             50.0      0.0    1.0           51.0     0.0                0.0   0.0   51.0
     5 2014-01-29 KNTCRK01G01H663X Clark Kent             150.0      0.0    3.0          153.0     0.0                0.0   2.0  155.0
TOTALE                                                    425.0      0.0    8.5          433.5     0.0                0.0   7.0  440.5
=== Febbraio ===
N.DOC. DATA       CODICE FISCALE   NOME       COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
     6 2014-02-28 KNTCRK01G01H663X Clark Kent    120.0     30.0    3.0          153.0   33.66               30.0  30.0 246.66
TOTALE                                           120.0     30.0    3.0          153.0   33.66               30.0  30.0 246.66
=== Marzo ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Aprile ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Maggio ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Giugno ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Luglio ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Agosto ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Settembre ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Ottobre ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Novembre ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
=== Dicembre ===
N.DOC. DATA CODICE FISCALE NOME COMPENSO RIMBORSI C.P.A. IMPONIBILE IVA IVA 22% ES.IVA ART.10 R.A. BOLLI TOTALE
TOTALE                               0.0      0.0    0.0            0.0     0.0                0.0   0.0    0.0
""")

    def test_invoice_main_summary_text(self):
        self._test_invoice_main_summary(table_mode=conf.TABLE_MODE_TEXT, pdata=False)

    def test_invoice_main_summary_xlsx(self):
        self._test_invoice_main_summary(table_mode=conf.TABLE_MODE_XLSX, pdata=False)

    def test_invoice_main_summary_xlsx_personal_data(self):
        self._test_invoice_main_summary(table_mode=conf.TABLE_MODE_XLSX, pdata=True)

    def test_invoice_main_list(self):
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

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'date, city,tax_code,year,number', '--filter', 'città != "Gotham City"', '-S', '2014-01-10', '-E', '2014-01-27'],
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
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--client', 'WNYBRC01G01H663S'],
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
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--client', 'PRKPRT01G01H663M,WNYBRC01G01H663S'],
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
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--client', 'PRKPRT01G01H663M,WNYBRC01G01H663S',
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
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--order', 'tax_code'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      5
KNTCRK01G01H663X 2014      6
PRKPRT01G01H663M 2014      2
WNYBRC01G01H663S 2014      1
WNYBRC01G01H663S 2014      4
""")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--order', 'tax_code,!date'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      6
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
                    args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--order', 'tax_code,!date', '--output', o_file.name],
                )
                self.assertEqual(p.string(), "")
                o_file.flush()
                with open(o_file.name, 'r') as f_in:
                    o_content = f_in.read()
                self.assertEqual(o_content, """\
codice_fiscale   anno numero
BNNBRC01G01H663S 2014      3
KNTCRK01G01H663X 2014      6
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
                    args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--order', 'tax_code,!date', '--output', o_filename_template, '--table-mode', conf.TABLE_MODE_XLSX],
                )
                try:
                    self.assertEqual(p.string(), "")
                    self.assertTrue(os.path.exists(o_filename))
                finally:
                    os.remove(o_filename)

    def test_invoice_main_dry_run(self):
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
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), "")

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['scan', '-R', rc_dir, '--dry-run', '--progressbar=off'],
            )

            p.reset()
            invoice_main(
                printer=p,
                logger=self.logger,
                args=['list', '-R', rc_dir, '--fields', 'tax_code,year,number', '--header=off'],
            )
            self.assertEqual(p.string(), "")

    def _test_invoice_main_global_options(self, *global_options):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            p = StringPrinter()

            args = ['init'] + list(global_options) + ['-R', rc_dir, os.path.join(self.dirname, '*.doc')]
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
[016] l'incasso non corrisponde alla somma delle singole componenti
[017] la CPA non è consistente con quanto dichiarato
[018] l'IVA non è consistente con quanto dichiarato
[019] la ritenuta d'acconto non è consistente con quanto dichiarato
[020] non è possibile convertire correttamente il valore di un campo della fattura
[021] manca il bollo di 2 euro per prestazione superiore a 77.47 euro
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
