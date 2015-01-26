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
    'InvoiceCollection',
]

from .error import InvoiceError, \
                   InvoiceSyntaxError, \
                   InvoiceMultipleNamesError, \
                   InvoiceUndefinedFieldError, \
                   InvoiceDateError, \
                   InvoiceDuplicatedNumberError, \
                   InvoiceWrongNumberError, \
                   InvoiceUnsupportedCurrencyError

from .invoice import Invoice
from .log import get_default_logger

class InvoiceCollection(object):
    def __init__(self, init=None, logger=None):
        self._invoices = []
        self._processed = False
        self._years = []
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        if init:
            for invoice in init:
                self.add(invoice)

    def __iter__(self):
        return iter(self._invoices)

    def __len__(self):
        return len(self._invoices)

    def __getitem__(self, index):
        return self._invoices[index]

    def add(self, invoice):
        if not isinstance(invoice, Invoice):
            raise TypeError("{}.add(...): oggetto {!r} di tipo {} non valido".format(self.__class__.__name__, invoice, type(invoice).__name__))
        self._invoices.append(invoice)

    def filter(self, filter_function):
        invoice_collection = InvoiceCollection(filter(filter_function, self._invoices), logger=self.logger)
        invoice_collection.process()
        return invoice_collection

    @classmethod
    def subst_None(cls, value, substitution):
        if value is None:
            return substitution
        else:
            return value

    def process(self):
        if not self._processed:
            self._invoices.sort(key=lambda invoice: self.subst_None(invoice.number, -1))
            self._invoices.sort(key=lambda invoice: self.subst_None(invoice.year, -1))
            self._years = tuple(sorted(set(invoice.year for invoice in self._invoices if invoice.year is not None)))
            self._processed = True

    def years(self):
        return self._years

