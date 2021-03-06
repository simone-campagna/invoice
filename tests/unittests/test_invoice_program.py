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
import glob
import io
import os
import shutil
import tempfile
import unittest

from invoice.log import get_null_logger
from invoice.error import InvoiceDuplicatedNumberError, \
                          InvoiceDuplicatedLineError, \
                          InvoiceDateError, \
                          InvoiceWrongNumberError, \
                          InvoiceUndefinedFieldError, \
                          InvoiceMultipleNamesError, \
                          InvoiceMultipleTaxCodesError, \
                          InvoiceMultipleInvoicesPerDayError, \
                          InvoiceMalformedTaxCodeError, \
                          InvoiceVersionError, \
                          InvoiceArgumentError, \
                          InvoiceInconsistentIncomeError, \
                          InvoiceInconsistentVatError, \
                          InvoiceInconsistentCpaError, \
                          InvoiceInconsistentDeductionError

from invoice.invoice_program import InvoiceProgram
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice import Invoice
from invoice.database.db_types import Path
from invoice.database.db import DbError
from invoice.validation_result import ValidationResult
from invoice.string_printer import StringPrinter
from invoice.version import Version
from invoice import conf

class TestInvoiceProgram(unittest.TestCase):
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

    REPORT_OUTPUT_2012 = """\
anno                       2012
  * incasso totale:        0.00
  * numero di fatture:     1
  * numero di clienti:     1
    + cliente:             PRKPRT01A01B123M (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      0.00
      incasso percentuale: 0.00%
      settimane:           2

  * numero di settimane:   1
    + settimana:           2 [2012-01-02 -> 2012-01-08]:
      numero di fatture:   1
      giorni:              2015-01-04 DO[1]
      incasso totale:      0.00
      incasso percentuale: 0.00%

"""

    STATS_OUTPUT_YEAR = """\
anno        da:         a: clienti fatture incasso %incasso
2014 2014-01-01 2014-12-31       4       6  687.16  100.00%
"""

    STATS_OUTPUT_YEAR_TOTAL = """\
anno          da:         a: clienti fatture incasso %incasso
2014   2014-01-01 2014-12-31       4       6  687.16  100.00%
TOTALE                             4       6  687.16  100.00%
"""
    STATS_OUTPUT_MONTH = """\
mese           da:         a: clienti fatture incasso %incasso
2014-01 2014-01-01 2014-01-31       4       5  440.50   64.10%
2014-02 2014-02-01 2014-02-28       1       1  246.66   35.90%
"""

    STATS_OUTPUT_MONTH_TOTAL = STATS_OUTPUT_MONTH + """\
TOTALE                              4       6  687.16  100.00%
"""

    STATS_OUTPUT_WEEK = """\
settimana        da:         a: clienti fatture incasso %incasso
2014:01   2014-01-01 2014-01-05       2       2  127.50   18.55%
2014:04   2014-01-20 2014-01-26       2       2  158.00   22.99%
2014:05   2014-01-27 2014-02-02       1       1  155.00   22.56%
2014:09   2014-02-24 2014-03-02       1       1  246.66   35.90%
"""

    STATS_OUTPUT_WEEK_TOTAL = STATS_OUTPUT_WEEK + """\
TOTALE                                4       6  687.16  100.00%
"""

    STATS_OUTPUT_DAY = """\
giorno            da:         a: clienti fatture incasso %incasso
2014-01-03 2014-01-03 2014-01-03       2       2  127.50   18.55%
2014-01-22 2014-01-22 2014-01-22       1       1  107.00   15.57%
2014-01-25 2014-01-25 2014-01-25       1       1   51.00    7.42%
2014-01-29 2014-01-29 2014-01-29       1       1  155.00   22.56%
2014-02-28 2014-02-28 2014-02-28       1       1  246.66   35.90%
"""
    STATS_OUTPUT_DAY_TOTAL = STATS_OUTPUT_DAY + """\
TOTALE                                 4       6  687.16  100.00%
"""

    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self._invoice_001_peter_parker = Invoice(
            doc_filename='2015_001_peter_parker.doc',
            year=2015, number=1,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1),
            service='therapy A',
            fee=200.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=202.0, currency='euro')
        self._invoice_002_peter_parker = Invoice(
            doc_filename='2015_002_peter_parker.doc',
            year=2015, number=2,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 2),
            service='therapy B',
            fee=100.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=102.0, currency='euro')
        self._invoice_003_peter_parker = Invoice(
            doc_filename='2015_003_peter_parser.doc',
            year=2015, number=3,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 3),
            service='therapy A',
            fee=150.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=152.0, currency='euro')
        self._invoices = [
            self._invoice_001_peter_parker,
            self._invoice_002_peter_parker,
            self._invoice_003_peter_parker,
        ]
        self._invoice_004_parker_peter = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Parker B. Peter', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 4),
            service='therapy A',
            fee=200.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=202.0, currency='euro')
        self._invoice_004_peter_parker_wrong_date = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 2),
            service='therapy B',
            fee=200.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=202.0, currency='euro')
        self._invoice_004_peter_parker_wrong_number = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=6,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 5),
            service='therapy B',
            fee=200.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=202.0, currency='euro')
        self._invoice_004_peter_parker_duplicated_number = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=self._invoices[-1].number,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 5),
            service='therapy A',
            fee=200.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=2.0,
            income=202.0, currency='euro')

    def test_InvoiceProgram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()

            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            p.reset()
            invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
                progressbar=False,
            )

            p.reset()
            invoice_program.impl_list(
                list_field_names=('tax_code', 'year', 'number'),
                header=True,
                filters=(),
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
            invoice_program.impl_dump(
                filters=(),
            )
            self.maxDiff = None
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)
            p.reset()
            invoice_program.impl_report()
            print(p.string().replace(self.dirname, '<DIRNAME>'))
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_program.impl_list(
                list_field_names=None,
                header=False,
                filters=(),
            )

    def test_InvoiceProgramDbNotExists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()

            i = 0
            while True:
                non_existent_filename = "{}.{}".format(db_filename, i)
                if not os.path.exists(non_existent_filename):
                    break
                i = i + 1
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=non_existent_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            with self.assertRaises(DbError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                    error_mode=None,
                    partial_update=None,
                    remove_orphaned=None,
                    progressbar=False,
                )

    def test_InvoiceProgramDbNotInitialized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            with self.assertRaises(DbError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                    error_mode=None,
                    partial_update=None,
                    remove_orphaned=None,
                    progressbar=False,
                )


    def test_InvoiceProgramInvalidVersion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            invoice_program.db.store_version(version=Version(0, 2, 0))

            p.reset()
            with self.assertRaises(InvoiceVersionError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                    error_mode=None,
                    partial_update=None,
                    remove_orphaned=None,
                    progressbar=False,
                )

    def test_InvoiceProgramOk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            docs_pattern = os.path.join(self.dirname, '*.doc')
            p.reset()
            invoice_program.impl_init(
                patterns=[docs_pattern],
                reset=True,
            )

            p.reset()
            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=(ValidationResult.ERROR_ACTION_RAISE,),
                progressbar=False,
            )
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(scan_events['added'], len(glob.glob(docs_pattern)))
            self.assertEqual(scan_events['modified'], 0)
            self.assertEqual(scan_events['removed'], 0)

            p.reset()
            invoice_program.impl_validate(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=(ValidationResult.ERROR_ACTION_RAISE,),
            )
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)

    def _test_InvoiceProgramSkip(self, reverse):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            include_docs_pattern = os.path.join(self.dirname, '*.doc')
            exclude_docs_pattern = os.path.join(self.dirname, '*kent*.doc')
            patterns=[include_docs_pattern, '!' + exclude_docs_pattern]
            if reverse:
                patterns.reverse()
                num_added_files = len(glob.glob(include_docs_pattern))
            else:
                num_added_files = len(glob.glob(include_docs_pattern)) - len(glob.glob(exclude_docs_pattern))

               
            p.reset()
            invoice_program.impl_init(
                patterns=patterns,
                reset=True,
            )

            p.reset()
            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=(ValidationResult.ERROR_ACTION_RAISE,),
                progressbar=False,
            )
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(scan_events['added'], num_added_files)
            self.assertEqual(scan_events['modified'], 0)
            self.assertEqual(scan_events['removed'], 0)

            p.reset()
            invoice_program.impl_list(
                list_field_names=('tax_code', 'year', 'number'),
                header=True,
                filters=(),
            )
            cmp_text = """\
codice_fiscale   anno numero
WNYBRC01G01H663S 2014      1
PRKPRT01G01H663M 2014      2
BNNBRC01G01H663S 2014      3
WNYBRC01G01H663S 2014      4
"""
            if reverse:
                cmp_text += """\
KNTCRK01G01H663X 2014      5
KNTCRK01G01H663X 2014      6
"""
            self.assertEqual(p.string(), cmp_text)

    def test_InvoiceProgramSkip(self):
        self._test_InvoiceProgramSkip(reverse=False)

    def test_InvoiceProgramSkipReverse(self):
        self._test_InvoiceProgramSkip(reverse=True)

    def test_InvoiceProgramErrorDuplicatedNumber(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_duplicated_number/*.doc')],
                reset=True,
            )

            p.reset()
            with self.assertRaises(InvoiceDuplicatedNumberError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                    error_mode=(ValidationResult.ERROR_ACTION_RAISE,),
                    progressbar=False,
                )

    def test_InvoiceProgramErrorDuplicatedLine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_duplicated_line/*.doc')],
                reset=True,
            )

            p.reset()
            with self.assertRaises(InvoiceDuplicatedLineError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                    error_mode=(ValidationResult.ERROR_ACTION_RAISE,),
                    progressbar=False,
                )

    def test_InvoiceProgram_validate_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices, logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)
    
    def test_InvoiceProgram_validate_warning_multiple_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_parker_peter], logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 1)
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertEqual(doc_filename, self._invoice_004_parker_peter.doc_filename)
    
    def test_InvoiceProgram_validate_error_wrong_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_date], logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_date.doc_filename)
                for error in errors:
                    self.assertIs(error.exc_type, InvoiceDateError)
            self.assertEqual(validation_result.num_warnings(), 2)
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertTrue(doc_filename in [self._invoice_004_peter_parker_wrong_date.doc_filename, self._invoice_002_peter_parker.doc_filename])
                for warning in warnings:
                    self.assertIs(warning.exc_type, InvoiceMultipleInvoicesPerDayError)
    
    def test_InvoiceProgram_validate_error_wrong_number(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_number], logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_number.doc_filename)
                self.assertEqual(len(errors), 1)
                exc_type, message = errors[0]
                self.assertIs(exc_type, InvoiceWrongNumberError)
    
    def test_InvoiceProgram_validate_error_duplicated_number(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_duplicated_number], logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_duplicated_number.doc_filename)
                self.assertEqual(len(errors), 1)
                exc_type, message = errors[0]
                self.assertIs(exc_type, InvoiceDuplicatedNumberError)
        
    def _test_InvoiceProgram_uf_mt(self, warning_action, wsuppress=False, esuppress=False):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Peter B. Parker', tax_code='WNYBRC01G01H663S', 
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=None, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=None, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a], logger=self.logger)
        
            error_action = ValidationResult.DEFAULT_ERROR_ACTION

            warning_mode = [warning_action]
            error_mode = []

            expected_errors = []
            expected_warnings = []

            expected_errors.append(InvoiceInconsistentIncomeError)
            if esuppress:
                error_mode.append("{}:{}".format(ValidationResult.ERROR_ACTION_IGNORE, InvoiceUndefinedFieldError.exc_code()))
            else:
                expected_errors.append(InvoiceUndefinedFieldError)
                expected_errors.append(InvoiceUndefinedFieldError)

            if wsuppress:
                warning_mode.append("{}:{}".format(ValidationResult.WARNING_ACTION_IGNORE, InvoiceMultipleTaxCodesError.exc_code()))
            else:
                if warning_action == ValidationResult.DEFAULT_WARNING_ACTION:
                    expected_warnings.append(InvoiceMultipleTaxCodesError)
                elif warning_action == ValidationResult.WARNING_ACTION_ERROR:
                    expected_errors.append(InvoiceMultipleTaxCodesError)
                elif warning_action == ValidationResult.WARNING_ACTION_IGNORE:
                    pass

            validation_result = invoice_program.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)

            print("warning_action={}, wsuppress={}, esuppress={}, warning_mode={}, error_mode={}, expected_warnings={}, expected_errors={}".format(
                warning_action,
                wsuppress,
                esuppress,
                warning_mode,
                error_mode,
                expected_warnings,
                expected_errors,
            ))
            for c, entries in enumerate(validation_result.warnings().values()):
                for entry in entries:
                    exc = entry.exc_type
                    print(" w {:2d} {} {}".format(c, exc.exc_code(), exc.__name__))
            for c, entries in enumerate(validation_result.errors().values()):
                for entry in entries:
                    exc = entry.exc_type
                    print(" e {:2d} {} {}".format(c, exc.exc_code(), exc.__name__))

            self.assertEqual(validation_result.num_errors(), len(expected_errors))
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, invoice_a.doc_filename)
                self.assertEqual(len(errors), len(expected_errors))
                exc_types = [error[0] for error in errors]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_errors)

            self.assertEqual(validation_result.num_warnings(), len(expected_warnings))
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertEqual(doc_filename, invoice_a.doc_filename)
                self.assertEqual(len(warnings), len(expected_warnings))
                exc_types = [warning[0] for warning in warnings]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_warnings)
           
    def test_InvoiceProgram_uf_mt_default(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.DEFAULT_WARNING_ACTION)
    
    def test_InvoiceProgram_uf_mt_default_ws(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.DEFAULT_WARNING_ACTION, wsuppress=True)
    
    def test_InvoiceProgram_uf_mt_default_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.DEFAULT_WARNING_ACTION, esuppress=True)
    
    def test_InvoiceProgram_uf_mt_default_ws_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.DEFAULT_WARNING_ACTION, wsuppress=True, esuppress=True)
    
    def test_InvoiceProgram_uf_mt_error(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_ERROR)

    def test_InvoiceProgram_uf_mt_error_ws(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_ERROR, wsuppress=True)

    def test_InvoiceProgram_uf_mt_error_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_ERROR, esuppress=True)

    def test_InvoiceProgram_uf_mt_error_ws_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_ERROR, wsuppress=True, esuppress=True)

    def test_InvoiceProgram_uf_mt_ignore(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_IGNORE)

    def test_InvoiceProgram_uf_mt_ignore_ws(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_IGNORE, wsuppress=True)

    def test_InvoiceProgram_uf_mt_ignore_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_IGNORE, esuppress=True)

    def test_InvoiceProgram_uf_mt_ignore_ws_es(self):
        self._test_InvoiceProgram_uf_mt(warning_action=ValidationResult.WARNING_ACTION_IGNORE, wsuppress=True, esuppress=True)

    def _test_InvoiceProgram_uf_mn(self, warning_action):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Parker B. Peter', tax_code='PRKPRT01G01H663M', 
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=None, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=None, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a], logger=self.logger)
        
            validation_result = invoice_program.create_validation_result(warning_mode=(warning_action,))
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)

            expected_errors = []
            expected_warnings = []
            expected_errors.append(InvoiceUndefinedFieldError)
            expected_errors.append(InvoiceUndefinedFieldError)
            expected_errors.append(InvoiceInconsistentIncomeError)
            if warning_action == ValidationResult.DEFAULT_WARNING_ACTION:
                expected_warnings.append(InvoiceMultipleNamesError)
            elif warning_action == ValidationResult.WARNING_ACTION_ERROR:
                expected_errors.append(InvoiceMultipleNamesError)
            elif warning_action == ValidationResult.WARNING_ACTION_IGNORE:
                pass

            self.assertEqual(validation_result.num_errors(), len(expected_errors))
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, invoice_a.doc_filename)
                self.assertEqual(len(errors), len(expected_errors))
                exc_types = [error[0] for error in errors]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_errors)

            self.assertEqual(validation_result.num_warnings(), len(expected_warnings))
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertEqual(doc_filename, invoice_a.doc_filename)
                self.assertEqual(len(warnings), len(expected_warnings))
                exc_types = [warning[0] for warning in warnings]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_warnings)
           
    def test_InvoiceProgram_uf_mn_default(self):
        self._test_InvoiceProgram_uf_mn(warning_action=ValidationResult.DEFAULT_WARNING_ACTION)
    
    def test_InvoiceProgram_uf_mn_error(self):
        self._test_InvoiceProgram_uf_mn(warning_action=ValidationResult.WARNING_ACTION_ERROR)

    def test_InvoiceProgram_uf_mn_ignore(self):
        self._test_InvoiceProgram_uf_mn(warning_action=ValidationResult.WARNING_ACTION_IGNORE)

    def _test_InvoiceProgram_mi(self, warning_action):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=20.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=20.0, currency='euro')
            invoice_b = Invoice(
                doc_filename='2015_005_parker_peter.doc',
                year=2015, number=5,
                name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=20.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=20.0, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a, invoice_b], logger=self.logger)
        
            validation_result = invoice_program.create_validation_result(warning_mode=(warning_action,))
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)

            expected_errors = []
            expected_warnings = []
            if warning_action == ValidationResult.DEFAULT_WARNING_ACTION:
                expected_warnings.append(InvoiceMultipleInvoicesPerDayError)
                expected_warnings.append(InvoiceMultipleInvoicesPerDayError)
            elif warning_action == ValidationResult.WARNING_ACTION_ERROR:
                expected_errors.append(InvoiceMultipleInvoicesPerDayError)
                expected_errors.append(InvoiceMultipleInvoicesPerDayError)
            elif warning_action == ValidationResult.WARNING_ACTION_IGNORE:
                pass

            self.assertEqual(validation_result.num_errors(), len(expected_errors))
            for doc_filename, errors in validation_result.errors().items():
                self.assertTrue(doc_filename in [invoice_a.doc_filename, invoice_b.doc_filename])
                self.assertEqual(len(errors), len(expected_errors))
                exc_types = [error[0] for error in errors]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_errors)

            self.assertEqual(validation_result.num_warnings(), len(expected_warnings))
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertTrue(doc_filename in [invoice_a.doc_filename, invoice_b.doc_filename])
                self.assertEqual(len(warnings), len(expected_warnings))
                exc_types = [warning[0] for warning in warnings]
                for exc_type in exc_types:
                    self.assertIn(exc_type, expected_warnings)
           
    def test_InvoiceProgram_mi_default(self):
        self._test_InvoiceProgram_mi(warning_action=ValidationResult.DEFAULT_WARNING_ACTION)
    
    def test_InvoiceProgram_mi_error(self):
        self._test_InvoiceProgram_mi(warning_action=ValidationResult.WARNING_ACTION_ERROR)

    def test_InvoiceProgram_mi_ignore(self):
        self._test_InvoiceProgram_mi(warning_action=ValidationResult.WARNING_ACTION_IGNORE)

    def test_InvoiceProgram_malformed_tax_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_malformed_tax_code', '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
                progressbar=False,
            )

            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 1)
            for doc_filename, errors in validation_result.errors().items():
                for error in errors:
                    self.maxDiff = None
                    self.assertIs(error.exc_type, InvoiceMalformedTaxCodeError)
                    self.assertEqual(error.message.replace(self.dirname, '<DIRNAME>'), "fattura <DIRNAME>/error_malformed_tax_code/2013_001_bruce_wayne.doc: codice fiscale 'WnYBRCO1GO10663T' non corretto: i caratteri non corretti sono 'W[n]YBRC[O]1G[O]1[0]663T'")

    def test_InvoiceProgram_zero_income(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
                progressbar=False,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

            invoice_collection.add(Invoice(
                doc_filename='2012_001_peter_parker.doc',
                year=2012, number=1,
                name='Peter B. Parker', tax_code='PRKPRT01A01B123M',
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=0.0, p_cpa=0.0, cpa=0.0, p_vat=0.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=0.0, currency='euro'))

            p.reset()
            invoice_collection = invoice_collection.filter("anno == 2012")
            invoice_program.report_invoice_collection(invoice_collection)
            self.maxDiff = None
            self.assertEqual(p.string(), self.REPORT_OUTPUT_2012)

    def test_InvoiceProgram_rescan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_filename = os.path.join(tmpdir, "test.db")
            example_dirname = os.path.join(tmpdir, "example")
            staged_doc_filenames = []
            os.makedirs(example_dirname)
            for doc_filename in glob.glob(os.path.join(self.dirname, "*.doc")):
                staged_doc_filename = os.path.join(example_dirname, os.path.basename(doc_filename))
                staged_doc_filenames.append(staged_doc_filename)
                shutil.copy(doc_filename, staged_doc_filename)

            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_program.impl_init(
                patterns=[os.path.join(example_dirname, '*.doc')],
                reset=True,
                partial_update=True,
            )

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                progressbar=False,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

            for doc_filename in glob.glob(os.path.join(self.dirname, "*002*.doc")):
                staged_doc_filename = os.path.join(example_dirname, os.path.basename(doc_filename))
                staged_doc_filenames.append(staged_doc_filename)
                shutil.copy(doc_filename, staged_doc_filename)

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                progressbar=False,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

    def _test_InvoiceProgram_remove_orphaned(self, remove_orphaned):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_filename = os.path.join(tmpdir, "test.db")
            example_dirname = os.path.join(tmpdir, "example")
            staged_doc_filenames = []
            os.makedirs(example_dirname)
            for doc_filename in glob.glob(os.path.join(self.dirname, "*.doc")):
                staged_doc_filename = os.path.join(example_dirname, os.path.basename(doc_filename))
                staged_doc_filenames.append(staged_doc_filename)
                shutil.copy(doc_filename, staged_doc_filename)

            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_program.impl_init(
                patterns=[os.path.join(example_dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=remove_orphaned,
            )

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
                progressbar=False,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(scan_events['added'], 6)
            self.assertEqual(scan_events['modified'], 0)
            self.assertEqual(scan_events['removed'], 0)

            p.reset()
            invoice_program.impl_dump(
                filters=(),
            )
            self.assertEqual(p.string().replace(example_dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_program.impl_report()
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            num_removed = 0
            for staged_doc_filename in staged_doc_filenames:
                os.remove(staged_doc_filename)
                num_removed += 1
            os.rmdir(example_dirname)

            validation_result, scan_events, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
                progressbar=False,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(scan_events['added'], 0)
            self.assertEqual(scan_events['modified'], 0)
            if remove_orphaned:
                self.assertEqual(scan_events['removed'], num_removed)
            else:
                self.assertEqual(scan_events['removed'], 0)

            p.reset()
            invoice_program.impl_dump(
                filters=(),
            )
            if remove_orphaned:
                self.assertEqual(p.string().replace(example_dirname, '<DIRNAME>'), "")
            else:
                self.assertEqual(p.string().replace(example_dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

    def test_InvoiceProgram_remove_orphaned_on(self):
        self._test_InvoiceProgram_remove_orphaned(True)

    def test_InvoiceProgram_remove_orphaned_off(self):
        self._test_InvoiceProgram_remove_orphaned(False)

    def _test_InvoiceProgram_stats(self, stats_group, expected_output, total):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
            )

            p.reset()
            invoice_program.impl_scan(
                warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                error_mode=None,
                progressbar=False,
            )

            p.reset()
            invoice_program.impl_stats(
                filters=(),
                stats_group=stats_group,
                total=total,
            )
            self.maxDiff = None
            print(p.string())
            self.assertEqual(p.string(), expected_output)

    def test_InvoiceProgram_stats_YEAR(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_YEAR,
            expected_output=self.STATS_OUTPUT_YEAR,
            total=False)

    def test_InvoiceProgram_stats_YEAR_total(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_YEAR,
            expected_output=self.STATS_OUTPUT_YEAR_TOTAL,
            total=True)

    def test_InvoiceProgram_stats_MONTH(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_MONTH,
            expected_output=self.STATS_OUTPUT_MONTH,
            total=False)

    def test_InvoiceProgram_stats_MONTH_total(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_MONTH,
            expected_output=self.STATS_OUTPUT_MONTH_TOTAL,
            total=True)

    def test_InvoiceProgram_stats_WEEK(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_WEEK,
            expected_output=self.STATS_OUTPUT_WEEK,
            total=False)

    def test_InvoiceProgram_stats_WEEK_total(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_WEEK,
            expected_output=self.STATS_OUTPUT_WEEK_TOTAL,
            total=True)

    def test_InvoiceProgram_stats_DAY(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_DAY,
            expected_output=self.STATS_OUTPUT_DAY,
            total=False)

    def test_InvoiceProgram_stats_DAY_total(self):
        self._test_InvoiceProgram_stats(
            stats_group=conf.STATS_GROUP_DAY,
            expected_output=self.STATS_OUTPUT_DAY_TOTAL,
            total=True)

    def test_InvoiceProgram_xlsx_mode_raises(self):
        p = StringPrinter()
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )
            with self.assertRaises(InvoiceArgumentError):
                invoice_program.impl_list(table_mode=conf.TABLE_MODE_XLSX)

    def test_InvoiceProgram_warning_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Peter B. Parker', tax_code='WNYBRC01G01H663S', 
                city='New York', date=datetime.date(2015, 1, 4),
                service='therapy',
                fee=80.0, p_cpa=0.0, cpa=0.0, p_vat=25.0, vat=0.0, p_deduction=0.0, deduction=0.0,
                refunds=0.0, taxes=0.0,
                income=100, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a], logger=self.logger)
        
            validation_result = invoice_program.create_validation_result(warning_mode=(ValidationResult.WARNING_ACTION_RAISE,))
            with self.assertRaises(InvoiceMultipleTaxCodesError):
                invoice_program.validate_invoice_collection(validation_result, invoice_collection)

    def _test_InvoiceProgram_inconsistency_errors(self, invoice, error_type):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)
            conf.setup(rc_dir=rc_dir)
            db_filename = conf.get_db_file()
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_filename,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [invoice], logger=self.logger)
        
            validation_result = invoice_program.create_validation_result(error_mode=(ValidationResult.ERROR_ACTION_RAISE,))
            with self.assertRaises(error_type):
                invoice_program.validate_invoice_collection(validation_result, invoice_collection)

    def test_InvoiceProgram_InvoiceInconsistentIncomeError(self):
        invoice = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 4),
            service='therapy',
            fee=80.0, p_cpa=0.0, cpa=0.0, p_vat=10.0, vat=8.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=0.0,
            income=100, currency='euro')
        self._test_InvoiceProgram_inconsistency_errors(invoice, InvoiceInconsistentIncomeError)

    def test_InvoiceProgram_InvoiceInconsistentVatError(self):
        invoice = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 4),
            service='therapy',
            fee=80.0, p_cpa=0.0, cpa=0.0, p_vat=10.0, vat=20.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=0.0,
            income=100, currency='euro')
        self._test_InvoiceProgram_inconsistency_errors(invoice, InvoiceInconsistentVatError)

    def test_InvoiceProgram_InvoiceInconsistentCpaError(self):
        invoice = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 4),
            service='therapy',
            fee=80.0, p_cpa=5.0, cpa=20.0, p_vat=25.0, vat=25.0, p_deduction=0.0, deduction=0.0,
            refunds=0.0, taxes=0.0,
            income=125, currency='euro')
        self._test_InvoiceProgram_inconsistency_errors(invoice, InvoiceInconsistentCpaError)

    def test_InvoiceProgram_InvoiceInconsistentDeductionError(self):
        invoice = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 4),
            service='therapy',
            fee=80.0, p_cpa=25.0, cpa=20.0, p_vat=25.0, vat=25.0, p_deduction=10.0, deduction=7.0,
            refunds=0.0, taxes=0.0,
            income=132, currency='euro')
        self._test_InvoiceProgram_inconsistency_errors(invoice, InvoiceInconsistentDeductionError)
