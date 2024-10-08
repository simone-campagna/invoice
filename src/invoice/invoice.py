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
                   InvoiceInconsistentIncomeError, \
                   InvoiceInconsistentCpaError, \
                   InvoiceInconsistentVatError, \
                   InvoiceInconsistentDeductionError, \
                   InvoiceMissingTaxError, \
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


def _cin_personal(tax_code):
    # control internal number for personal tax_code
    s = 0
    for c, symbol in enumerate(tax_code[:-1]):
        s += _TAX_CODE_EVEN_ODD[symbol][(c + 1) % 2]
    cin = _TAX_CODE_CONTROL_LETTER[s % 26]
    return cin


def _cin_luhn(tax_code):
    # control internal number for vat number
    digits = [int(i) for i in tax_code]
    control_digit = digits.pop(-1)
    value_x = sum(digits[0::2])
    value_y = sum(((2 * i) % 9) for i in digits[1::2])
    value_t = (value_x + value_y) % 10
    value_c = (10 - value_t) % 10
    return str(value_c)


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
            d['Date'] = lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date()
            d['Weekday'] = conf.WEEKDAY_NUMBER
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
        income_parts = conf.DERIVATIVES['income']
        income_values = [getattr(self, part) for part in income_parts]
        expected_income = sum(v for v in income_values if v is not None)
        if expected_income != self.income:
            parts = " ".join("{}:{}".format(part, income) for part, income in zip(income_parts, income_values))
            validation_result.add_error(
                    invoice=self,
                    exc_type=InvoiceInconsistentIncomeError,
                    message="fattura {}: incasso non coerente: {} - totale:{} - atteso:{}".format(self.doc_filename, parts, self.income, expected_income))
        ndecimals = 2
        change_date = datetime.date(2024, 10, 7)  # after this date, the cpa must be computed including the taxes (a.k.a. bolli)
        for key in "cpa", "vat", "deduction":
            source_fields = list(conf.DERIVATIVES[key])
            if self.date >= change_date:
                source_fields.append('taxes')
            p_key = "p_" + key
            percentage = getattr(self, p_key)
            if percentage is not None:
                val = round(getattr(self, key), ndecimals)
                if key == "vat":
                    error_class = InvoiceInconsistentVatError
                else:
                    if key == "cpa":
                       error_class = InvoiceInconsistentCpaError
                    elif key == "deduction":
                       error_class = InvoiceInconsistentDeductionError
                       val = -val
                source_vals = [getattr(self, source_field) for source_field in source_fields]
                source_val = round(sum(v for v in source_vals if v is not None), ndecimals)
                expected_val = round(source_val * percentage / 100.0, ndecimals)
                if expected_val != val:
                    source_text = " + ".join("{}[{}]".format(v, self.get_field_translation(f)) for v, f in zip(source_vals, source_fields))
                    validation_result.add_error(
                            invoice=self,
                            exc_type=error_class,
                            message="fattura {d}: {f} {v} non corretto: sorgente: {s} = {t} - percentuale: {p}% - atteso:{e}".format(
                                d=self.doc_filename,
                                f=self.get_field_translation(key),
                                v=val,
                                s=source_text,
                                t=source_val,
                                p=percentage,
                                e=expected_val))
            
        if self.fee is not None:
            taxable_income = sum(getattr(self, key) for key in conf.DERIVATIVES['vat'])
            if taxable_income > 77.47 and self.vat == 0 and self.deduction == 0:
                if self.taxes < 2:
                    if self.exceptions:
                        exceptions = self.exceptions.split(',')
                    else:
                        exceptions = []
                    if 'no-bollo' not in exceptions:
                        message = "fattura {}: imponibile={}, iva={}, ritenuta={}, bolli={}: è richiesto un bollo di almeno 2 euro".format(
                            self.doc_filename,
                            taxable_income,
                            self.vat,
                            self.deduction,
                            self.taxes,
                        )
                        validation_result.add_error(
                            invoice=self,
                            exc_type=InvoiceMissingTaxError,
                            message=message)

        tax_code = self.tax_code
        if tax_code:
            valid_tax_code = True
            # length check

            cin_function = None
            if valid_tax_code:
                # è una partita iva?
                if len([ch for ch in tax_code if ch not in set('0123456789')]) == 0:
                    # partita iva
                    cin_function = _cin_luhn
                    if len(tax_code) != 11:
                        message = "fattura {}: partita iva {!r} non corretto: la lunghezza è {!r}, non 11 come richiesto".format(
                            self.doc_filename,
                            tax_code,
                            len(tax_code),
                        )
                        validation_result.add_error(
                            invoice=self,
                            exc_type=InvoiceMalformedTaxCodeError,
                            message=message)
                        valid_tax_code = False
                else:
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
                    else:
                        cin_function = _cin_personal
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
                cin = cin_function(tax_code)
                if cin != tax_code[-1]:
                    message = "fattura {}: codice fiscale {!r} non corretto: il carattere di controllo è {!r}, non {!r} come atteso".format(
                        self.doc_filename,
                        tax_code,
                        tax_code[-1],
                        cin,
                    )
                    validation_result.add_error(
                        invoice=self,
                        exc_type=InvoiceMalformedTaxCodeError,
                        message=message)
        return validation_result

