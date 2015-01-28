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
    'Invoice',
]

import collections

from .error import InvoiceUndefinedFieldError, \
                   InvoiceUnsupportedCurrencyError, \
                   InvoiceYearError, \
                   InvoiceMalformedTaxCodeError

from .validation_result import ValidationResult

InvoiceNamedTuple = collections.namedtuple('InvoiceNamedTuple', (
    'doc_filename',
    'year',
    'number',
    'name',
    'tax_code',
    'city',
    'date',
    'income',
    'currency',
))


_FIELD_TRANSLATION = {
    'doc_filename': 'documento',
    'year':         'anno',
    'number':       'numero',
    'name':         'nome',
    'tax_code':     'codice_fiscale',
    'city':         'città',
    'date':         'data',
    'income':       'importo',
    'currency':     'valuta',
}


class Invoice(InvoiceNamedTuple):
    FIELD_TRANSLATION = _FIELD_TRANSLATION
    REV_FIELD_TRANSLATION = dict(
        (_FIELD_TRANSLATION.get(field_name, field_name), field_name) for field_name in InvoiceNamedTuple._fields
    )
    ALL_FIELDS = set(tuple(InvoiceNamedTuple._fields) + tuple(REV_FIELD_TRANSLATION.keys()))

    def _asdict(self):
        return collections.OrderedDict(((field, getattr(self, field)) for field in self._fields))
    __dict__ = property(_asdict)

    @classmethod
    def get_field_translation(cls, field_name):
        return cls.FIELD_TRANSLATION.get(field_name, field_name)

    @classmethod
    def get_field_name_from_translation(cls, field_translation):
        return cls.REV_FIELD_TRANSLATION.get(field_translation, field_translation)

    def validate(self, validation_result):
        for key in self._fields:
            val = getattr(self, key)
            if val is None:
                validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceUndefinedFieldError,
                    message="fattura {}: il campo {!r} non è definito".format(self.doc_filename, self.get_field_translation(key)))
        if self.currency != 'euro':
            validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceUnsupportedCurrencyError,
                    message="fattura {}: la valuta {!r} non è supportata".format(self.doc_filename, self.currency))
        if self.date is not None and self.date.year != self.year:
            validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceYearError,
                    message="fattura {}: data {} e anno {} sono incompatibili".format(self.doc_filename, self.date, self.year))

        tax_code = self.tax_code
        if tax_code:
            expected_ch = 'LLLLLLNNLNNLNNNL'
            error_fmt = '[{}]'
            success_fmt = '{}'
            error_l = []
            num_errors = 0
            for ch, expected_ch in zip(tax_code, expected_ch):
                error = False
                if expected_ch == 'L' and not (ord('A') <= ord(ch) <= ord('Z')):
                    error = True
                elif expected_ch == 'N' and not (ord('0') <= ord(ch) <= ord('9')):
                    error = True
                if error:
                    error_l.append(error_fmt.format(ch))
                    num_errors += 1
                else:
                    error_l.append(success_fmt.format(ch))
            if num_errors:
                message = "fattura {}: codice fiscale {!r} non corretto: i caratteri non corretti sono {!r}".format(
                    self.doc_filename,
                    tax_code,
                    ''.join(error_l),
                )
                validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceMalformedTaxCodeError,
                    message=message)
        return validation_result

