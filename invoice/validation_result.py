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
    'ValidationResult',
]

import collections

class ValidationResult(object):
    def __init__(self):
        self._failing_invoices = set()
        self._errors = collections.OrderedDict()
        self._warnings = collections.OrderedDict()

    def filter_validated_invoices(self, invoices):
        validated_invoices = []
        for invoice in invoices:
            if not invoice.doc_filename in self._failing_invoices:
                validated_invoices.append(invoice)
        return validated_invoices

    def failing_invoices(self):
        return self._failing_invoices

    def add_error(self, invoice, message):
        self._errors.setdefault(invoice.doc_filename, []).append(message)
        self._failing_invoices.add(invoice.doc_filename)

    def add_warning(self, invoice, message):
        self._warnings.setdefault(invoice.doc_filename, []).append(message)

    def __bool__(self):
        return len(self._errors) == 0

    def num_errors(self):
        return sum(len(l) for l in self._errors.values())

    def num_warnings(self):
        return sum(len(l) for l in self._warnings.values())

    def errors(self):
        return self._errors

    def warnings(self):
        return self._warnings
