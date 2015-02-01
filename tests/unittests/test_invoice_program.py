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
                          InvoiceDateError, \
                          InvoiceWrongNumberError, \
                          InvoiceUndefinedFieldError, \
                          InvoiceMultipleNamesError, \
                          InvoiceMalformedTaxCodeError

from invoice.invoice_program import InvoiceProgram
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice import Invoice
from invoice.database.db_types import Path
from invoice.database.db import DbError
from invoice.validation_result import ValidationResult
from invoice.string_printer import StringPrinter

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
  * incasso totale:        433.00
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

    REPORT_OUTPUT_2012 = """\
anno                       2012
  * incasso totale:        0.00
  * numero di fatture:     1
  * numero di clienti:     1
    + cliente:             PRKPRT01A01B123C (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      0.00
      incasso percentuale: 0.00%
      settimane:           2

  * numero di settimane:   1
    + settimana:           2 [2012-01-02 -> 2012-01-08]:
      numero di fatture:   1
      incasso totale:      0.00
      incasso percentuale: 0.00%

"""
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        self._invoice_001_peter_parker = Invoice(
            doc_filename='2015_001_peter_parker.doc',
            year=2015, number=1,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 1),
            income=200.0, currency='euro')
        self._invoice_002_peter_parker = Invoice(
            doc_filename='2015_002_peter_parker.doc',
            year=2015, number=2,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 2),
            income=100.0, currency='euro')
        self._invoice_003_peter_parker = Invoice(
            doc_filename='2015_003_peter_parser.doc',
            year=2015, number=3,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 3),
            income=150.0, currency='euro')
        self._invoices = [
            self._invoice_001_peter_parker,
            self._invoice_002_peter_parker,
            self._invoice_003_peter_parker,
        ]
        self._invoice_004_parker_peter = Invoice(
            doc_filename='2015_004_parker_peter.doc',
            year=2015, number=4,
            name='Parker B. Peter', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 4),
            income=200.0, currency='euro')
        self._invoice_004_peter_parker_wrong_date = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=4,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 2),
            income=200.0, currency='euro')
        self._invoice_004_peter_parker_wrong_number = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=6,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 5),
            income=200.0, currency='euro')
        self._invoice_004_peter_parker_duplicated_number = Invoice(
            doc_filename='2015_004_peter_parker.doc',
            year=2015, number=self._invoices[-1].number,
            name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 5),
            income=200.0, currency='euro')

    def test_InvoiceProgram(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
            )

            p.reset()
            invoice_program.impl_list(
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
            invoice_program.impl_dump(
                filters=(),
            )
            self.assertEqual(p.string().replace(self.dirname, '<DIRNAME>'), self.DUMP_OUTPUT)
            p.reset()
            invoice_program.impl_report()
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            p.reset()
            invoice_program.impl_list(
                field_names=None,
                header=False,
                filters=(),
            )

    def test_InvoiceProgramNotInitialized(self):
        with tempfile.NamedTemporaryFile() as db_file:
            i = 0
            while True:
                non_existent_filename = "{}.{}".format(db_file, i)
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
                    warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                    error_mode=None,
                    partial_update=None,
                    remove_orphaned=None,
                )

    def test_InvoiceProgramInvalidVersion(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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

            invoice_program.db.store_version(version=invoice_program.db.Version(0, 2, 0))

            p.reset()
            with self.assertRaises(DbError):
                invoice_program.impl_scan(
                    warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                    error_mode=None,
                    partial_update=None,
                    remove_orphaned=None,
                )

    def test_InvoiceProgramOk(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
            )

            p.reset()
            validation_result, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=ValidationResult.ERROR_MODE_RAISE,
            )
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)

            p.reset()
            invoice_program.impl_validate(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=ValidationResult.ERROR_MODE_RAISE,
            )
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)

    def test_InvoiceProgramError(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
                    warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                    error_mode=ValidationResult.ERROR_MODE_RAISE,
                )

    def test_InvoiceProgram_validate_ok(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_date], logger=self.logger)
            validation_result = invoice_program.create_validation_result()
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_date.doc_filename)
                for error in errors:
                    self.assertIs(error.exc_type, InvoiceDateError)
    
    def test_InvoiceProgram_validate_error_wrong_number(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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
        
    def _test_InvoiceProgram_undefined_field(self, warning_mode):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
                logger=self.logger,
                trace=False,
                printer=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Parker B. Peter', tax_code='PRKPRT01A01B123C', 
                city='New York', date=datetime.date(2015, 1, 4),
                income=None, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a], logger=self.logger)
        
            validation_result = invoice_program.create_validation_result(warning_mode=warning_mode)
            invoice_program.validate_invoice_collection(validation_result, invoice_collection)

            expected_errors = []
            expected_warnings = []
            expected_errors.append(InvoiceUndefinedFieldError)
            if warning_mode == ValidationResult.WARNING_MODE_DEFAULT:
                expected_warnings.append(InvoiceMultipleNamesError)
            elif warning_mode == ValidationResult.WARNING_MODE_ERROR:
                expected_errors.append(InvoiceMultipleNamesError)
            elif warning_mode == ValidationResult.WARNING_MODE_IGNORE:
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
           
    def test_InvoiceProgram_undefined_field_default(self):
        self._test_InvoiceProgram_undefined_field(warning_mode=ValidationResult.WARNING_MODE_DEFAULT)
    
    def test_InvoiceProgram_undefined_field_error(self):
        self._test_InvoiceProgram_undefined_field(warning_mode=ValidationResult.WARNING_MODE_ERROR)

    def test_InvoiceProgram_undefined_field_ignore(self):
        self._test_InvoiceProgram_undefined_field(warning_mode=ValidationResult.WARNING_MODE_IGNORE)

    def test_InvoiceProgram_malformed_tax_code(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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

            validation_result, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
            )

            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 1)
            for doc_filename, errors in validation_result.errors().items():
                for error in errors:
                    self.assertIs(error.exc_type, InvoiceMalformedTaxCodeError)
                    self.assertEqual(error.message.replace(self.dirname, '<DIRNAME>'), "fattura <DIRNAME>/error_malformed_tax_code/2013_001_bruce_wayne.doc: codice fiscale 'WnYBRCO1GO10663Y' non corretto: i caratteri non corretti sono 'W[n]YBRC[O]1G[O]1[0]663Y'")

    def test_InvoiceProgram_zero_income(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()
            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
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

            validation_result, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

            invoice_collection.add(Invoice(
                doc_filename='2012_001_peter_parker.doc',
                year=2012, number=1,
                name='Peter B. Parker', tax_code='PRKPRT01A01B123C',
                city='New York', date=datetime.date(2015, 1, 4),
                income=0.0, currency='euro'))

            p.reset()
            invoice_collection = invoice_collection.filter("anno == 2012")
            invoice_program.report_invoice_collection(invoice_collection)
            self.assertEqual(p.string(), self.REPORT_OUTPUT_2012)

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

            validation_result, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

            p.reset()
            invoice_program.impl_dump(
                filters=(),
            )
            self.assertEqual(p.string().replace(example_dirname, '<DIRNAME>'), self.DUMP_OUTPUT)

            p.reset()
            invoice_program.impl_report()
            self.assertEqual(p.string(), self.REPORT_OUTPUT)

            for staged_doc_filename in staged_doc_filenames:
                os.remove(staged_doc_filename)
            os.rmdir(example_dirname)

            validation_result, invoice_collection = invoice_program.impl_scan(
                warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                error_mode=None,
                partial_update=None,
                remove_orphaned=None,
            )
            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 0)

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
