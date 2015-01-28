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
from invoice.error import InvoiceDuplicatedNumberError, \
                          InvoiceWrongNumberError, \
                          InvoiceUndefinedFieldError, \
                          InvoiceMultipleNamesError, \
                          InvoiceMalformedTaxCodeError

from invoice.invoice_program import InvoiceProgram
from invoice.invoice_collection import InvoiceCollection
from invoice.invoice import Invoice
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

    def test_InvoiceProgram_validate_ok(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices, logger=self.logger)
            validation_result = invoice_program.validate_invoice_collection(invoice_collection)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 0)
    
    def test_InvoiceProgram_validate_warning_multiple_names(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_parker_peter], logger=self.logger)
            validation_result = invoice_program.validate_invoice_collection(invoice_collection)
            self.assertEqual(validation_result.num_errors(), 0)
            self.assertEqual(validation_result.num_warnings(), 1)
            for doc_filename, warnings in validation_result.warnings().items():
                self.assertEqual(doc_filename, self._invoice_004_parker_peter.doc_filename)
    
    def test_InvoiceProgram_validate_error_wrong_date(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_date], logger=self.logger)
            validation_result = invoice_program.validate_invoice_collection(invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_date.doc_filename)
    
    def test_InvoiceProgram_validate_error_wrong_number(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_number], logger=self.logger)
            validation_result = invoice_program.validate_invoice_collection(invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_number.doc_filename)
                self.assertEqual(len(errors), 1)
                exc_type, message = errors[0]
                self.assertIs(exc_type, InvoiceWrongNumberError)
    
    def test_InvoiceProgram_validate_error_duplicated_number(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_duplicated_number], logger=self.logger)
            validation_result = invoice_program.validate_invoice_collection(invoice_collection)
            self.assertEqual(validation_result.num_errors(), 1)
            self.assertEqual(validation_result.num_warnings(), 0)
            for doc_filename, errors in validation_result.errors().items():
                self.assertEqual(doc_filename, self._invoice_004_peter_parker_duplicated_number.doc_filename)
                self.assertEqual(len(errors), 1)
                exc_type, message = errors[0]
                self.assertIs(exc_type, InvoiceDuplicatedNumberError)
        
    def _test_InvoiceProgram_undefined_field(self, warnings_mode):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_a = Invoice(
                doc_filename='2015_004_parker_peter.doc',
                year=2015, number=4,
                name='Parker B. Peter', tax_code='PRKPRT01A01B123C', 
                city='New York', date=datetime.date(2015, 1, 4),
                income=None, currency='euro')
            invoice_collection = InvoiceCollection(self._invoices + [invoice_a], logger=self.logger)
        
            validation_result = invoice_program.validate_invoice_collection(invoice_collection, warnings_mode=warnings_mode)
            #print("warnings_mode={}".format(warnings_mode))
            #print("errors=", validation_result.errors())
            #print("warnings=", validation_result.warnings())

            expected_errors = []
            expected_warnings = []
            expected_errors.append(InvoiceUndefinedFieldError)
            if warnings_mode == InvoiceProgram.WARNINGS_MODE_DEFAULT:
                expected_warnings.append(InvoiceMultipleNamesError)
            elif warnings_mode == InvoiceProgram.WARNINGS_MODE_ERROR:
                expected_errors.append(InvoiceMultipleNamesError)
            elif warnings_mode == InvoiceProgram.WARNINGS_MODE_IGNORE:
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
        self._test_InvoiceProgram_undefined_field(warnings_mode=InvoiceProgram.WARNINGS_MODE_DEFAULT)
    
    def test_InvoiceProgram_undefined_field_error(self):
        self._test_InvoiceProgram_undefined_field(warnings_mode=InvoiceProgram.WARNINGS_MODE_ERROR)

    def test_InvoiceProgram_undefined_field_ignore(self):
        self._test_InvoiceProgram_undefined_field(warnings_mode=InvoiceProgram.WARNINGS_MODE_IGNORE)

    def test_InvoiceProgram_malformed_tax_code(self):
        with tempfile.NamedTemporaryFile() as db_filename:
            p = Print()
            invoice_program = InvoiceProgram(
                db_filename=db_filename.name,
                logger=self.logger,
                trace=False,
                print_function=p,
            )
    
            invoice_program.db_init(
                patterns=[os.path.join(self.dirname, '*.doc'), os.path.join(self.dirname, 'error_malformed_tax_code', '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            validation_result, invoice_collection = invoice_program.db_scan(
                warnings_mode=InvoiceProgram.WARNINGS_MODE_DEFAULT,
                raise_on_error=False,
                partial_update=None,
                remove_orphaned=None,
            )

            self.assertEqual(validation_result.num_warnings(), 0)
            self.assertEqual(validation_result.num_errors(), 1)
            for doc_filename, errors in validation_result.errors().items():
                for error in errors:
                    self.assertIs(error.exc_type, InvoiceMalformedTaxCodeError)
                    self.assertEqual(error.message.replace(self.dirname, '<DIRNAME>'), "fattura <DIRNAME>/error_malformed_tax_code/2013_001_bruce_wayne.doc: codice fiscale 'WNYBRCO1GO10663Y' non corretto: i caratteri non corretti sono '______O__O_0____'")
