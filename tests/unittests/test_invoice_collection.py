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
    'TestInvoice',
]

import datetime
import unittest

from invoice.invoice import Invoice
from invoice.invoice_collection import InvoiceCollection

class TestInvoice(unittest.TestCase):
    def setUp(self):
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
        self._invoice_003_parker_peter = Invoice(
            doc_filename='2015_003_parker_peter.doc',
            year=2015, number=3,
            name='Parker B. Peter', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 3),
            income=200.0, currency='euro')

    # invoice
    def test_InvoiceCollection_default(self):
        invoice_collection = InvoiceCollection()
        
    def test_InvoiceCollection_init(self):
        invoice_collection = InvoiceCollection([
            self._invoice_001_peter_parker,
            self._invoice_002_peter_parker,
            self._invoice_003_parker_peter,
        ])

    def test_filter(self):
        invoice_collection = InvoiceCollection([
            self._invoice_001_peter_parker,
            self._invoice_002_peter_parker,
            self._invoice_003_parker_peter,
        ])
        self.assertEqual(len(invoice_collection), 3)
        invoice_collection_2 = invoice_collection.filter("number != 2")
        self.assertEqual(len(invoice_collection_2), 2)
        invoice_collection_3 = invoice_collection.filter(lambda invoice: invoice.number != 2)
        self.assertEqual(len(invoice_collection_3), 2)
        with self.assertRaises(NameError):
            invoice_collection_4 = invoice_collection.filter("numer != 2")
