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

import collections
import datetime
import math

from .error import InvoiceError, \
                   InvoiceMultipleNamesError, \
                   InvoiceUndefinedFieldError, \
                   InvoiceDateError, \
                   InvoiceDuplicatedNumberError, \
                   InvoiceWrongNumberError, \
                   InvoiceUnsupportedCurrencyError

from .invoice import Invoice
from .validation_result import ValidationResult
from .log import get_default_logger
from .week import WeekManager

class InvoiceCollection(object):
    WARNINGS_MODE_DEFAULT = 'default'
    WARNINGS_MODE_ERROR = 'error'
    WARNINGS_MODE_IGNORE = 'ignore'
    WARNINGS_MODES = (WARNINGS_MODE_DEFAULT, WARNINGS_MODE_ERROR, WARNINGS_MODE_IGNORE)

    LIST_FIELD_NAMES_SHORT = ('year', 'number', 'date', 'tax_code', 'income', 'currency')
    LIST_FIELD_NAMES_LONG = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
    LIST_FIELD_NAMES_FULL = Invoice._fields

    FIELD_HEADERS = {
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

    def __init__(self, init=None, logger=None):
        self._invoices = []
        self._processed = False
        self._years = []
        self._week_manager = WeekManager()
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        if init:
            for invoice in init:
                self.add(invoice)

    @classmethod
    def compile_filter_function(cls, function_source):
        def filter(invoice):
            d = invoice._asdict()
            for field_name, name in cls.FIELD_HEADERS.items():
                if field_name != name:
                    d[name] = d[field_name]
            locals().update(datetime=datetime, **d)
            return eval(function_source)
        return filter

    @classmethod
    def get_field_name(cls, field_name):
        return cls.FIELD_HEADERS.get(field_name, field_name)

    def __iter__(self):
        return iter(self._invoices)

    def __len__(self):
        return len(self._invoices)

    def __getitem__(self, index):
        return self._invoices[index]

    def add(self, invoice):
        if not isinstance(invoice, Invoice):
            raise TypeError("invalid object {!r} of type {} (not an Invoice)".format(invoice, type(invoice).__name__))
        self._invoices.append(invoice)

    def filter(self, function):
        if isinstance(function, str):
            function = self.compile_filter_function(function)
        invoice_collection = InvoiceCollection(filter(function, self._invoices), logger=self.logger)
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

    def log_critical(self, invoice, exc_type, message, result):
        self.logger.critical(message)
        result.add_error(invoice, exc_type, message)
        raise exc_type(message)
        
    def log_error(self, invoice, exc_type, message, result):
        self.logger.error(message)
        result.add_error(invoice, exc_type, message)
        return result

    def log_warning(self, invoice, exc_type, message, result):
        self.logger.warning(message)
        result.add_warning(invoice, exc_type, message)
        return result

    def log_functions(self, result, warnings_mode=None, raise_on_error=False):
        if warnings_mode is None:
            warnings_mode = self.WARNINGS_MODE_DEFAULT
        if raise_on_error:
            log_error = lambda invoice, exc_type, message: self.log_critical(invoice, exc_type, message, result=result)
        else:
            log_error = lambda invoice, exc_type, message: self.log_error(invoice, exc_type, message, result=result)
        if warnings_mode == self.WARNINGS_MODE_ERROR:
            log_warning = log_error
        elif warnings_mode == self.WARNINGS_MODE_IGNORE:
            def log_warning(invoice, exc_type, message):
                pass
        elif warnings_mode == self.WARNINGS_MODE_DEFAULT:
            log_warning = lambda invoice, exc_type, message: self.log_warning(invoice, exc_type, message, result=result)
        else:
            raise ValueError("invalid warnings mode {!r}".format(warnings_mode))
        return log_error, log_warning

    def validate_invoice(self, result, warnings_mode=None, raise_on_error=False):
        log_error, log_warning = self.log_functions(result=result, warnings_mode=warnings_mode, raise_on_error=raise_on_error)
        return self.impl_validate_invoice(invoice, result, log_error, log_warning)

    def impl_validate_invoice(self, invoice, result, log_error, log_warning):
        for key in 'year', 'number', 'name', 'tax_code', 'date', 'income':
            val = getattr(invoice, key)
            if val is None:
                log_error(invoice, InvoiceUndefinedFieldError, "fattura {}: il campo {!r} non è definito".format(invoice.doc_filename, self.get_field_name(key)))
        if invoice.currency != 'euro':
            log_error(invoice, InvoiceUnsupportedCurrencyError, "fattura {}: la valuta {!r} non è supportata".format(invoice.doc_filename, invoice.currency))
        if invoice.date is not None and invoice.date.year != invoice.year:
            log_error(invoice, InvoiceDateError, "fattura {}: data {} e anno {} sono incompatibili".format(invoice.doc_filename, invoice.date, invoice.year))
        return result

    def validate(self, warnings_mode=None, raise_on_error=False):
        result = ValidationResult()
        self.process()
        log_error, log_warning = self.log_functions(result=result, warnings_mode=warnings_mode, raise_on_error=raise_on_error)

        # verify fields definition:
        for invoice in self._invoices:
            self.impl_validate_invoice(invoice, result, log_error, log_warning)

        # verify first/last name exchange:
        nd = {}
        for invoice in self._invoices:
            if invoice.tax_code in nd:
                i_name, i_doc_filenames = nd[invoice.tax_code]
                if i_name != invoice.name:
                    log_warning(invoice, InvoiceMultipleNamesError, "fattura {f}: il codice_fiscale {t!r} è associato al nome {n!r}, mentre è stato associato ad un altro nome {pn!r} in #{c} fatture".format(
                        f=invoice.doc_filename,
                        t=invoice.tax_code,
                        n=invoice.name,
                        pn=i_name,
                        c=len(i_doc_filenames),
                    ))
            else:
                nd[invoice.tax_code] = (invoice.name, [invoice.doc_filename])

        # verify numbering and dates per year
        for year in self.years():
            invoices = self.filter(lambda invoice: invoice.year == year)
            numbers = set()
            expected_number = 0
            prev_doc, prev_date = None, None
            for invoice in invoices:
                expected_number += 1
                if invoice.number != expected_number:
                    if invoice.number in numbers:
                        log_error(invoice, InvoiceDuplicatedNumberError,
                            "fattura {}: il numero {} è duplicato".format(invoice.doc_filename, invoice.number, year, expected_number))
                    else:
                        log_error(invoice, InvoiceWrongNumberError,
                            "fattura {}: il numero {} non è valido (il numero atteso per l'anno {} è {})".format(invoice.doc_filename, invoice.number, year, expected_number))
                else:
                    numbers.add(invoice.number)
                if prev_date is not None:
                    if invoice.date < prev_date:
                        log_error(invoice, InvoiceDateError, "fattura {}: la data {} precede quella della precedente fattura {} ({})".format(invoice.doc_filename, invoice.date, prev_doc, prev_date))
                prev_doc, prev_date = invoice.doc_filename, invoice.date

        
        return result

    def list(self, field_names, header=True, print_function=print):
        if field_names is None:
            field_names = Invoice._fields
        self.process()
        data = []
        digits =1 + int(math.log10(max(1, len(self._invoices))))
        converters = {
            'number': lambda n: "{n:0{digits}d}".format(n=n, digits=digits),
            'income': lambda i: "{:.2f}".format(i),
        }
        aligns = {
            'number': '>',
            'income': '>',
        }
        if header:
            data.append(tuple(self.get_field_name(field_name) for field_name in field_names))
        for invoice in self._invoices:
            data.append(tuple(converters.get(field_name, str)(getattr(invoice, field_name)) for field_name in field_names))
        if data:
            lengths = [max(len(row[c]) for row in data) for c, f in enumerate(field_names)]
            fmt = " ".join("{{row[{i}]:{align}{{lengths[{i}]}}s}}".format(i=i, align=aligns.get(f, '<')) for i, f in enumerate(field_names))
            for row in data:
                print_function(fmt.format(row=row, lengths=lengths))

    def dump(self, print_function=print):
        self.process()
        digits = 1 + int(math.log10(max(1, len(self._invoices))))
        for invoice in self._invoices:
            print_function("""\
fattura:                   {doc_filename!r}
  anno/numero:             {year}/{number:0{digits}d}
  città/data:              {city}/{date}
  nome:                    {name}
  codice fiscale:          {tax_code}
  importo:                 {income:.2f} [{currency}]""".format(digits=digits, **invoice._asdict()))

    def report(self, print_function=print):
        self.process()
        for year in self.years():
            year_invoices = self.filter(lambda invoice: invoice.year == year)
            td = collections.OrderedDict()
            wd = collections.OrderedDict()
            for invoice in year_invoices:
                td.setdefault(invoice.tax_code, []).append(invoice)
                wd.setdefault(self.get_week_number(invoice.date), []).append(invoice)
            print_function("""\
anno                       {year}
  * numero di fatture:     {num_invoices}
  * numero di clienti:     {num_clients}\
""".format(
                year=year,
                num_invoices=len(year_invoices),
                num_clients=len(td),
            ))
            total_income = sum(invoice.income for invoice in year_invoices)
            for tax_code, invoices in td.items():
                client_total_income = sum(invoice.income for invoice in invoices)
                if total_income != 0.0:
                    client_income_percentage = client_total_income / total_income
                else:
                    client_income_percentage = 0.0
                client_weeks = sorted(set(self.get_week_number(invoice.date) for invoice in invoices))
                print_function("""\
    + cliente:             {tax_code} ({name}):
      numero di fatture:   {num_invoices}
      incasso totale:      {client_total_income}
      incasso percentuale: {client_income_percentage:.2%}
      settimane:           {client_weeks}
""".format(
                    tax_code=tax_code,
                    name='|'.join(name for name in set(invoice.name for invoice in invoices)),
                    num_invoices=len(invoices),
                    total_income=total_income,
                    client_total_income=client_total_income,
                    client_income_percentage=client_income_percentage,
                    client_weeks=', '.join(repr(week) for week in client_weeks),
                ))
            print_function("""\
  * numero di settimane:   {num_weeks}\
""".format(
                num_weeks=len(wd),
            ))
            for week in sorted(wd.keys()):
                invoices = wd[week]
                week_total_income = sum(invoice.income for invoice in invoices)
                if total_income != 0.0:
                    week_income_percentage = week_total_income / total_income
                else:
                    week_income_percentage = 0.0
                first_date, last_date = self.get_week_range(year, week)
                print_function("""\
    + settimana:           {week} [{first_date} -> {last_date}]:
      numero di fatture:   {num_invoices}
      incasso totale:      {week_total_income}
      incasso percentuale: {week_income_percentage:.2%}
""".format(
                    week=week,
                    num_invoices=len(invoices),
                    first_date=first_date,
                    last_date=last_date,
                    total_income=total_income,
                    week_total_income=week_total_income,
                    week_income_percentage=week_income_percentage,
                ))
        
    def get_week_number(self, day):
        return self._week_manager.week_number(day)

    def get_week_range(self, year, week_number):
        return self._week_manager.week_range(year=year, week_number=week_number)

