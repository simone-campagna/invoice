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
    'TestInvoiceCollection',
]

import datetime
import unittest

from invoice.log import get_null_logger
from invoice.invoice import Invoice
from invoice.invoice_collection import InvoiceCollection

class TestInvoiceCollection(unittest.TestCase):
    def setUp(self):
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
    def test_InvoiceCollection_default(self):
        invoice_collection = InvoiceCollection(logger=self.logger)
        
    def test_InvoiceCollection_init(self):
        invoice_collection = InvoiceCollection(self._invoices, logger=self.logger)

    def test_filter(self):
        invoice_collection = InvoiceCollection(self._invoices, logger=self.logger)
        self.assertEqual(len(invoice_collection), 3)
        invoice_collection_2 = invoice_collection.filter("number != 2")
        self.assertEqual(len(invoice_collection_2), 2)
        invoice_collection_3 = invoice_collection.filter(lambda invoice: invoice.number != 2)
        self.assertEqual(len(invoice_collection_3), 2)
        with self.assertRaises(NameError):
            invoice_collection_4 = invoice_collection.filter("numer != 2")

    def test_InvoiceCollection_validate_ok(self):
        invoice_collection = InvoiceCollection(self._invoices, logger=self.logger)
        validation_result = invoice_collection.validate()
        self.assertEqual(validation_result.num_errors(), 0)
        self.assertEqual(validation_result.num_warnings(), 0)

    def test_InvoiceCollection_validate_warning_multiple_names(self):
        invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_parker_peter], logger=self.logger)
        validation_result = invoice_collection.validate()
        self.assertEqual(validation_result.num_errors(), 0)
        self.assertEqual(validation_result.num_warnings(), 1)
        for doc_filename, warnings in validation_result.warnings().items():
            self.assertEqual(doc_filename, self._invoice_004_parker_peter.doc_filename)

    def test_InvoiceCollection_validate_error_wrong_date(self):
        invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_date], logger=self.logger)
        validation_result = invoice_collection.validate()
        self.assertEqual(validation_result.num_errors(), 1)
        self.assertEqual(validation_result.num_warnings(), 0)
        for doc_filename, errors in validation_result.errors().items():
            self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_date.doc_filename)

    def test_InvoiceCollection_validate_error_wrong_number(self):
        invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_wrong_number], logger=self.logger)
        validation_result = invoice_collection.validate()
        self.assertEqual(validation_result.num_errors(), 1)
        self.assertEqual(validation_result.num_warnings(), 0)
        for doc_filename, errors in validation_result.errors().items():
            self.assertEqual(doc_filename, self._invoice_004_peter_parker_wrong_number.doc_filename)

    def test_InvoiceCollection_validate_error_duplicated_number(self):
        invoice_collection = InvoiceCollection(self._invoices + [self._invoice_004_peter_parker_duplicated_number], logger=self.logger)
        validation_result = invoice_collection.validate()
        self.assertEqual(validation_result.num_errors(), 1)
        self.assertEqual(validation_result.num_warnings(), 0)
        for doc_filename, errors in validation_result.errors().items():
            self.assertEqual(doc_filename, self._invoice_004_peter_parker_duplicated_number.doc_filename)
        

