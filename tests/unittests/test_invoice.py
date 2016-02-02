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
                          InvoiceMalformedTaxCodeError, \
                          InvoiceMissingTaxError
from invoice.invoice import Invoice
from invoice.log import get_null_logger
from invoice.validation_result import ValidationResult

class TestInvoice(unittest.TestCase):
    def setUp(self):
        pass

    # invoice
    def test_Invoice(self):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=202.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=2.0,
            service='therapy')

    def test_InvoiceValidateOk(self):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=202.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=2.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        invoice.validate(validation_result)
        self.assertEqual(validation_result.num_errors(), 0)
        self.assertEqual(validation_result.num_warnings(), 0)

    def test_InvoiceValidateUndefinedField(self):
        invoice = Invoice(doc_filename='x.doc', year=None, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=202.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=2.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceUndefinedFieldError):
            invoice.validate(validation_result)

    def test_InvoiceValidateYearError(self):
        invoice = Invoice(doc_filename='x.doc', year=2013, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=205.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=5.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceYearError):
            invoice.validate(validation_result)

    def _test_InvoiceValidateMalformedTaxCode(self, tax_code):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code=tax_code, 
            city='New York', date=datetime.date(2015, 1, 1), fee=200.0, vat=0.0, cpa=0.0, deduction=0.0, income=202.0, currency='euro',
            p_vat=0.0, p_cpa=0.0, p_deduction=0.0, refunds=0.0, taxes=2.0,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        with self.assertRaises(InvoiceMalformedTaxCodeError):
            invoice.validate(validation_result)

    def _test_InvoiceMissingTaxError(self, fee, fail, *, p_cpa=0.0, p_vat=0.0, p_deduction=0.0, taxes=0.0, refunds=0.0):
        cpa = (fee + refunds) * p_cpa / 100.0
        vat = (fee + refunds + cpa) * p_vat / 100.0
        deduction = (fee + refunds) * p_deduction / 100.0
        income = fee + refunds + vat + deduction + taxes + cpa
        #print(fee, p_cpa, cpa, p_vat, vat, p_deduction, deduction, refunds, taxes)
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01G01H663M', 
            city='New York', date=datetime.date(2015, 1, 1), fee=fee, vat=vat, cpa=cpa, deduction=deduction, income=income, currency='euro',
            p_vat=p_vat, p_cpa=p_cpa, p_deduction=p_deduction, refunds=refunds, taxes=taxes,
            service='therapy')
        validation_result = ValidationResult(logger=get_null_logger(), error_mode=(ValidationResult.ERROR_ACTION_RAISE, ))
        if fail:
            with self.assertRaises(InvoiceMissingTaxError):
                invoice.validate(validation_result)
        else:
            invoice.validate(validation_result)

    def test_InvoiceMissingTaxError0(self):
        self._test_InvoiceMissingTaxError(fee=77.0, p_vat=0.0, p_deduction=0.0, taxes=0.0, fail=False)

    def test_InvoiceMissingTaxError1(self):
        self._test_InvoiceMissingTaxError(fee=77.48, p_vat=0.0, p_deduction=0.0, taxes=0.0, fail=True)

    def test_InvoiceMissingTaxError2(self):
        self._test_InvoiceMissingTaxError(fee=100, p_vat=22.0, p_deduction=0.0, taxes=0.0, fail=False)

    def test_InvoiceMissingTaxError3(self):
        self._test_InvoiceMissingTaxError(fee=100, p_vat=0.0, p_deduction=22.0, taxes=0.0, fail=False)

    def test_InvoiceMissingTaxError4(self):
        self._test_InvoiceMissingTaxError(fee=100, p_vat=0.0, p_deduction=0.0, taxes=1.9, fail=True)

    def test_InvoiceMissingTaxError5(self):
        self._test_InvoiceMissingTaxError(fee=100, p_vat=0.0, p_deduction=0.0, taxes=2.0, fail=False)

    def test_InvoiceMissingTaxError6(self):
        self._test_InvoiceMissingTaxError(fee=70.00, refunds=7.0, p_deduction=0.0, taxes=0.0, fail=False)

    def test_InvoiceMissingTaxError7(self):
        self._test_InvoiceMissingTaxError(fee=70.00, refunds=8.0, p_deduction=0.0, taxes=0.0, fail=True)

    def test_InvoiceMissingTaxError8(self):
        self._test_InvoiceMissingTaxError(fee=70.00, p_cpa=10.0, p_deduction=0.0, taxes=0.0, fail=False)

    def test_InvoiceMissingTaxError9(self):
        self._test_InvoiceMissingTaxError(fee=70.00, p_cpa=20.0, p_deduction=0.0, taxes=0.0, fail=True)

    def test_InvoiceMissingTaxError10(self):
        self._test_InvoiceMissingTaxError(fee=70.00, p_cpa=10.0, refunds=0.50, p_deduction=0.0, taxes=0.0, fail=True)

    def test_InvoiceValidateMalformedTaxCode_short(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRT01G0H663M')

    def test_InvoiceValidateMalformedTaxCode_long(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPURT01G01H663M')

    def test_InvoiceValidateMalformedTaxCode_symbols(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRTO1G01H663M')

    def test_InvoiceValidateMalformedTaxCode_control(self):
        self._test_InvoiceValidateMalformedTaxCode('PRKPRT01G01H663N')
