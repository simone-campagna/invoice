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

from invoice.error import InvoiceUndefinedFieldError, \
                          InvoiceYearError, \
                          InvoiceMalformedTaxCodeError
from invoice.invoice import Invoice
from invoice.log import get_null_logger
from invoice.validation_result import ValidationResult

class TestInvoice(unittest.TestCase):
    def setUp(self):
        pass

    # invoice
    def test_Invoice(self):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=200.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=0.0,
            service='therapy')

    def test_InvoiceValidateOk(self):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=200.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=0.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        invoice.validate(validation_result)
        self.assertEqual(validation_result.num_errors(), 0)
        self.assertEqual(validation_result.num_warnings(), 0)

    def test_InvoiceValidateUndefinedField(self):
        invoice = Invoice(doc_filename='x.doc', year=None, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=200.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=0.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceUndefinedFieldError):
            invoice.validate(validation_result)

    def test_InvoiceValidateYearError(self):
        invoice = Invoice(doc_filename='x.doc', year=2013, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=200.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=0.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceYearError):
            invoice.validate(validation_result)

    def _test_InvoiceValidateMalformedTaxCode(self, tax_code):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code=tax_code, 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=200.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=0.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceMalformedTaxCodeError):
            invoice.validate(validation_result)

    def test_InvoiceValidateMalformedTaxCode_short(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRT01G0H663M')

    def test_InvoiceValidateMalformedTaxCode_long(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPURT01G01H663M')

    def test_InvoiceValidateMalformedTaxCode_symbols(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRTO1G01H663M')

    def test_InvoiceValidateMalformedTaxCode_control(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRT01G01H663N')
