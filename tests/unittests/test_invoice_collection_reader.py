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
    'TestInvoiceCollectionReader',
]

import datetime
import os
import tempfile
import unittest

from invoice import conf
from invoice.log import get_null_logger
from invoice.invoice import Invoice
from invoice.invoice_collection_reader import InvoiceCollectionReader
from invoice.validation_result import ValidationResult

class TestInvoiceCollectionReader(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.join(os.path.dirname(__file__), '..', '..', 'example')
        self.logger = get_null_logger()

    def test_InvoiceCollectionReader_default(self):
        invoice_collection_reader = InvoiceCollectionReader(logger=self.logger)

    def test_InvoiceCollectionReader_default_logger(self):
        invoice_collection_reader = InvoiceCollectionReader()


    def test_InvoiceCollectionReader(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rc_dir = os.path.join(tmpdir, 'rc_dir')
            os.makedirs(rc_dir)

            conf.setup(rc_dir=rc_dir)

            doc_filename = os.path.normpath(os.path.abspath(os.path.join(self.dirname, '2014_001_bruce_wayne.doc')))
            glob_filename = doc_filename.replace('bruce_wayne', '*')
            validation_result = ValidationResult(logger=self.logger)
            invoice_collection_reader = InvoiceCollectionReader(logger=self.logger)
            invoice_collection = invoice_collection_reader(validation_result, glob_filename)
            self.assertEqual(len(invoice_collection), 1)
            invoice = invoice_collection[0]
            self.assertEqual(invoice.doc_filename, doc_filename)
            self.assertEqual(invoice.year, 2014)
            self.assertEqual(invoice.number, 1)
            self.assertEqual(invoice.city, 'Gotham City')
            self.assertEqual(invoice.date, datetime.date(2014, 1, 3))
            self.assertEqual(invoice.tax_code, "WNYBRC01G01H663S")
            self.assertEqual(invoice.name, "Bruce Wayne")
            self.assertEqual(invoice.income, 51.0)
            self.assertEqual(invoice.currency, "euro")
