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
import datetime

from .error import InvoiceUndefinedFieldError, \
                   InvoiceUnsupportedCurrencyError, \
                   InvoiceYearError, \
                   InvoiceTaxCodeError, \
                   InvoiceMalformedTaxCodeError, \
                   InvoiceSyntaxError

from .validation_result import ValidationResult
from . import conf

InvoiceNamedTuple = collections.namedtuple('InvoiceNamedTuple', conf.FIELD_NAMES)

_TAX_CODE_EVEN_ODD = {
    'A':	(0,	1),
    'B':	(1,	0),
    'C':	(2,	5),
    'D':	(3,	7),
    'E':	(4,	9),
    'F':	(5,	13),
    'G':	(6,	15),
    'H':	(7,	17),
    'I':	(8,	19),
    'J':	(9,	21),
    'K':	(10,	2),
    'L':	(11,	4),
    'M':	(12,	18),
    'N':	(13,	20),
    'O':	(14,	11),
    'P':	(15,	3),
    'Q':	(16,	6),
    'R':	(17,	8),
    'S':	(18,	12),
    'T':	(19,	14),
    'U':	(20,	16),
    'V':	(21,	10),
    'W':	(22,	22),
    'X':	(23,	25),
    'Y':	(24,	24),
    'Z':	(25,	23),
}

for digit in range(10):
    letter = chr(ord('A') + digit)
    _TAX_CODE_EVEN_ODD[str(digit)] = _TAX_CODE_EVEN_ODD[letter]

_TAX_CODE_CONTROL_LETTER = {i: chr(i + ord('A')) for i in range(26)}


class Invoice(InvoiceNamedTuple):
    def _asdict(self):
        return collections.OrderedDict(((field, getattr(self, field)) for field in self._fields))
    __dict__ = property(_asdict)

    @classmethod
    def get_field_translation(cls, field_name):
        return conf.FIELD_TRANSLATION.get(field_name, field_name)

    @classmethod
    def get_field_name_from_translation(cls, field_translation):
        return conf.REV_FIELD_TRANSLATION.get(field_translation, field_translation)

    @classmethod
    def compile_filter_function(cls, function_source):
        try:
            function_code = compile(function_source, '<string>', 'eval')
        except SyntaxError as err:
            raise InvoiceSyntaxError("funzione filtro {!r} non valida".format(function_source), "funzione filter non valida", function_source, err)
        def filter(invoice):
            d = invoice._asdict()
            for field_name, name in conf.FIELD_TRANSLATION.items():
                if field_name != name:
                    d[name] = d[field_name]
            locals().update(datetime=datetime, **d)
            return eval(function_code)
        return filter

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
            valid_tax_code = True
            # length check
            if len(tax_code) != 16:
                message = "fattura {}: codice fiscale {!r} non corretto: la lunghezza è {!r}, non 16 come richiesto".format(
                    self.doc_filename,
                    tax_code,
                    len(tax_code),
                )
                validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceMalformedTaxCodeError,
                    message=message)
                valid_tax_code = False

            if valid_tax_code:
                # symbols check
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
                    valid_tax_code = False

            if valid_tax_code:
                # control letter check
                s = 0
                for c, symbol in enumerate(tax_code[:-1]):
                    s += _TAX_CODE_EVEN_ODD[symbol][(c + 1) % 2]
                control_letter = _TAX_CODE_CONTROL_LETTER[s % 26]
                if control_letter != tax_code[-1]:
                    message = "fattura {}: codice fiscale {!r} non corretto: il carattere di controllo è {!r}, non {!r} come atteso".format(
                        self.doc_filename,
                        tax_code,
                        tax_code[-1],
                        control_letter,
                    )
                    validation_result.add_error(
                        invoice=self,
                        exc_type=InvoiceMalformedTaxCodeError,
                        message=message)
        return validation_result

