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

import datetime
import math

from .invoice import Invoice
from .log import get_default_logger
from .week import WeekManager

class InvoiceCollection(object):
    WARNINGS_MODE_DEFAULT = 'default'
    WARNINGS_MODE_ERROR = 'error'
    WARNINGS_MODE_IGNORE = 'ignore'
    WARNINGS_MODES = (WARNINGS_MODE_DEFAULT, WARNINGS_MODE_ERROR, WARNINGS_MODE_IGNORE)

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
            locals().update(datetime=datetime, **invoice._asdict())
            return eval(function_source)
        return filter

    def __iter__(self):
        return iter(self._invoices)

    def __len__(self):
        return len(self._invoices)

    def add(self, invoice):
        if not isinstance(invoice, Invoice):
            raise TypeError("invalid object {!r} of type {} (not an Invoice)".format(invoice, type(invoice).__name__))
        self._invoices.append(invoice)

    def filter(self, function):
        if isinstance(function, str):
            function = self.compile_filter_function(function)
        return InvoiceCollection(filter(function, self._invoices), logger=self.logger)

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

    def validate(self, warnings_mode=None, raise_on_error=False):
        self.process()
        if warnings_mode is None:
            warnings_mode = self.WARNINGS_MODE_DEFAULT

        result = dict(errors=0, warnings=0)
        def log_error(message):
            self.logger.error(message)
            if raise_on_error:
                raise InvoiceError(message)
            result['errors'] += 1

        if warnings_mode == self.WARNINGS_MODE_ERROR:
            log_warning = log_error
        elif warnings_mode == self.WARNINGS_MODE_IGNORE:
            def log_warning(message):
                pass
        elif warnings_mode == self.WARNINGS_MODE_DEFAULT:
            def log_warning(message):
                self.logger.warning(message)
                result['warnings'] += 1
        else:
            raise ValueError("invalid warnings mode {!r}".format(warnings_mode))


        # verify fields definition:
        for invoice in self._invoices:
            for key in 'year', 'number', 'name', 'tax_code', 'date', 'income':
                val = getattr(invoice, key)
                if val is None:
                    log_error("invoice {}: {} is undefined".format(invoice.doc_filename, key))
            if invoice.currency != 'euro':
                log_error("invoice {}: unsupported currency {!r}".format(invoice.doc_filename, invoice.currency))
            if invoice.date is not None and invoice.date.year != invoice.year:
                log_error("invoice {}: date {} does not match with year {}".format(invoice.doc_filename, invoice.date, invoice.year))

        # verify first/last name exchange:
        nd = {}
        for invoice in self._invoices:
            nd.setdefault(invoice.tax_code, set()).add(invoice.name)
        for tax_code, names in nd.items():
            if len(names) > 1:
                log_warning("#{} names ({}) refer to the same tax_code {}: possible first/last name exchange".format(len(names), ', '.join(repr(name) for name in names), tax_code))

        # verify numbering and dates per year
        for year in self.years():
            invoices = self.filter(lambda invoice: invoice.year == year)
            expected_number = 0
            prev_doc, prev_date = None, None
            for invoice in invoices:
                expected_number += 1
                if invoice.number != expected_number:
                    log_error("invoice {}: number {} is not valid (expected number for year {} is {})".format(invoice.doc_filename, invoice.number, year, expected_number))
                if prev_date is not None:
                    if invoice.date < prev_date:
                        log_error("invoice {}: date {} is lower than previous invoice {} ({})".format(invoice.doc_filename, invoice.date, prev_doc, prev_date))
                prev_doc, prev_date = invoice.doc_filename, invoice.date
        return result

    def list(self, print_function=print):
        self.process()
        digits = 1 + int(math.log10(max(1, len(self._invoices))))
        for invoice in self._invoices:
            print_function("""\
invoice:                  {doc_filename!r}
  year/number:            {year}/{number:0{digits}d}
  city/date:              {city}/{date}
  name:                   {name}
  tax code:               {tax_code}
  total income:           {income:.2f} [{currency}]""".format(digits=digits, **invoice._asdict()))

    def report(self, print_function=print):
        self.process()
        for year in self.years():
            year_invoices = self.filter(lambda invoice: invoice.year == year)
            td = {}
            wd = {}
            for invoice in year_invoices:
                td.setdefault(invoice.tax_code, []).append(invoice)
                wd.setdefault(self.get_week_number(invoice.date), []).append(invoice)
            print_function("""\
year {year}:
  * number_of invoices:   {num_invoices}
  * number of clients:    {num_clients}\
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
                print("""\
    + client:             {tax_code} ({name}):
      number of invoices: {num_invoices}
      total income:       {client_total_income}
      income percentage:  {client_income_percentage:.2%}
      weeks:              {client_weeks}
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
  * number of weeks:      {num_weeks}\
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
                print("""\
    + week:               {week} [{first_date} -> {last_date}]:
      number of invoices: {num_invoices}
      total income:       {week_total_income}
      income percentage:  {week_income_percentage:.2%}
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

