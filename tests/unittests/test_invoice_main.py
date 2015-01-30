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

class Test_invoice_main(unittest.TestCase):
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
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           1, 4

    + cliente:             PRKPRT01G01H663Y (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      76.50
      incasso percentuale: 17.67%
      settimane:           1

    + cliente:             BNNBRC01G01H663Y (Robert Bruce Banner):
      numero di fatture:   1
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           4

    + cliente:             KNTCRK01G01H663Y (Clark Kent):
      numero di fatture:   1
      incasso totale:      152.50
      incasso percentuale: 35.22%
      settimane:           5

  * numero di settimane:   3
    + settimana:           1 [2014-01-01 -> 2014-01-05]:
      numero di fatture:   2
      incasso totale:      127.50
      incasso percentuale: 29.45%

    + settimana:           4 [2014-01-20 -> 2014-01-26]:
      numero di fatture:   2
      incasso totale:      153.00
      incasso percentuale: 35.33%

    + settimana:           5 [2014-01-27 -> 2014-02-02]:
      numero di fatture:   1
      incasso totale:      152.50
      incasso percentuale: 35.22%

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
    CONFIG_ADD_PATTERNS = """\
patterns:
  + Pattern(pattern='<DIRNAME>/*.doc')
  + Pattern(pattern='<DIRNAME>/*.Doc')
  + Pattern(pattern='<DIRNAME>/*.DOC')

configuration:
  + remove_orphaned      = False
  + partial_update       = True
"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main(self):
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
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number'],
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
                args=['-d', db_filename.name, 'report', '-y', '2014'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'report', '-y', '2014,2015'],
            )
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--filter', 'number % 2 == 0', '--filter=tax_code.startswith("P")'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
PRKPRT01G01H663Y 2014      2
""")

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'validate'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'clear'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--no-header'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--no-header', '--filter', 'città == Rome'], # InvoiceSyntaxError
            )
            self.assertEqual(p.string(), '')

    def test_invoice_main_err(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_wrong_number', '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number'],
            )
            self.assertEqual(p.string(), """\
codice_fiscale   anno numero
WNYBRC01G01H663Y 2014      1
PRKPRT01G01H663Y 2014      2
BNNBRC01G01H663Y 2014      3
WNYBRC01G01H663Y 2014      4
KNTCRK01G01H663Y 2014      5
""")

    def test_invoice_main_err_partial_update_off(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'init', '--partial-update=off', os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_wrong_number', '*.doc')],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan'],
            )
            self.assertEqual(p.string(), '')

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--no-header'],
            )
            self.assertEqual(p.string(), '')

    def test_invoice_main_config_partial_update_on(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update=on', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_partial_update_off(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update=off', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_OFF)

    def test_invoice_main_config_partial_update(self):
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
                args=['-d', db_filename.name, 'config', '--partial-update', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config(self):
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
                args=['-d', db_filename.name, 'config', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_config_add_remove_patterns(self):
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
                args=['-d', db_filename.name, 'config', '-p', 'example/*.Doc', '-p', 'example/*.DOC', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_ADD_PATTERNS)

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'config', '-x', 'example/*.Doc', '-x', 'example/*.DOC', '--show'],
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.CONFIG_SHOW_PARTIAL_UPDATE_ON)

    def test_invoice_main_dry_run(self):
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
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--no-header'],
            )
            self.assertEqual(p.string(), "")

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'scan', '--dry-run'],
            )

            p.reset()
            invoice_main(
                print_function=p,
                logger=self.logger,
                args=['-d', db_filename.name, 'list', '--fields', 'tax_code,year,number', '--no-header'],
            )
            self.assertEqual(p.string(), "")

    def _test_invoice_main_global_options(self, *global_options):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()

            args = list(global_options) + ['-d', db_filename.name, 'init', os.path.join(self.dirname, '*.doc')]
            p.reset()
            invoice_main(
                print_function=p,
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

    def test_invoice_main_help(self):
        p = Print()

        p.reset()
        s = io.StringIO()
        invoice_main(
            print_function=p,
            stream=s,
            logger=self.logger,
            args=["help"]
        )

    def test_invoice_main_default_subcommand(self):
        p = Print()

        p.reset()
        s = io.StringIO()
        invoice_main(
            print_function=p,
            stream=s,
            logger=self.logger,
            args=[],
        )

