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
    'InvoiceProgram'
]

import collections
import datetime
import glob
import math
import os
import time
import traceback

from .error import InvoiceSyntaxError, \
                   InvoiceDateError, \
                   InvoiceMultipleNamesError, \
                   InvoiceWrongNumberError, \
                   InvoiceDuplicatedNumberError, \
                   InvoiceMalformedTaxCodeError, \
                   InvoiceValidationError

from .invoice_collection import InvoiceCollection
from .invoice_collection_reader import InvoiceCollectionReader
from .invoice_reader import InvoiceReader
from .invoice_db import InvoiceDb
from .invoice import Invoice
from .validation_result import ValidationResult
from .week import WeekManager
from .database.db_types import Path


class FileDateTimes(object):
    def __init__(self):
        self._date_times = {}

    def __getitem__(self, filename):
        if not filename in self._date_times:
            if os.path.exists(filename):
                self._date_times[filename] = datetime.datetime(*time.localtime(os.stat(filename).st_ctime)[:6])
            else:
                self._date_times[filename] = datetime.datetime.now()
        return self._date_times[filename]

class InvoiceProgram(object):
    LIST_FIELD_NAMES_SHORT = ('year', 'number', 'date', 'tax_code', 'income', 'currency')
    LIST_FIELD_NAMES_LONG = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
    LIST_FIELD_NAMES_FULL = Invoice._fields

    def __init__(self, db_filename, logger, print_function=print, trace=False):
        self.db_filename = db_filename
        self.logger = logger
        self.print_function = print_function
        self.trace = trace
        self.db = InvoiceDb(self.db_filename, self.logger)
        self._week_manager = WeekManager()

    def get_week_number(self, day):
        return self._week_manager.week_number(day)

    def get_week_range(self, year, week_number):
        return self._week_manager.week_range(year=year, week_number=week_number)

    def create_validation_result(self, warning_mode=None, error_mode=None):
        return ValidationResult(
            logger=self.logger,
            warning_mode=warning_mode,
            error_mode=error_mode,
        )
    def validate_invoice_collection(self, validation_result, invoice_collection):
        invoice_collection.process()

        # verify fields definition:
        for invoice in invoice_collection:
            invoice.validate(validation_result=validation_result)

        # verify first/last name exchange:
        nd = {}
        for invoice in invoice_collection:
            if invoice.tax_code in nd:
                i_name, i_doc_filenames = nd[invoice.tax_code]
                if i_name != invoice.name:
                    message = "fattura {f}: il codice_fiscale {t!r} è associato al nome {n!r}, mentre è stato associato ad un altro nome {pn!r} in #{c} fatture".format(
                        f=invoice.doc_filename,
                        t=invoice.tax_code,
                        n=invoice.name,
                        pn=i_name,
                        c=len(i_doc_filenames),
                    )
                    validation_result.add_warning(invoice, InvoiceMultipleNamesError, message)
            else:
                nd[invoice.tax_code] = (invoice.name, [invoice.doc_filename])

        # verify numbering and dates per year
        for year in invoice_collection.years():
            invoices = invoice_collection.filter(lambda invoice: invoice.year == year)
            numbers = set()
            expected_number = 0
            prev_doc, prev_date = None, None
            for invoice in invoices:
                expected_number += 1
                if invoice.number != expected_number:
                    if invoice.number in numbers:
                        validation_result.add_error(invoice, InvoiceDuplicatedNumberError,
                            "fattura {}: il numero {} è duplicato".format(invoice.doc_filename, invoice.number, year, expected_number))
                    else:
                        validation_result.add_error(invoice, InvoiceWrongNumberError,
                            "fattura {}: il numero {} non è valido (il numero atteso per l'anno {} è {})".format(invoice.doc_filename, invoice.number, year, expected_number))
                else:
                    numbers.add(invoice.number)
                if prev_date is not None:
                    if invoice.date is not None and invoice.date < prev_date:
                        validation_result.add_error(invoice, InvoiceDateError, "fattura {}: la data {} precede quella della precedente fattura {} ({})".format(invoice.doc_filename, invoice.date, prev_doc, prev_date))
                prev_doc, prev_date = invoice.doc_filename, invoice.date

        
        return validation_result

    def list_invoice_collection(self, invoice_collection, field_names, header=True):
        invoice_collection.process()
        if field_names is None:
            field_names = Invoice._fields
        field_names = [Invoice.get_field_name_from_translation(field_name) for field_name in field_names]
        data = []
        digits =1 + int(math.log10(max(1, len(invoice_collection))))
        converters = {
            'number': lambda n: "{n:0{digits}d}".format(n=n, digits=digits),
            'income': lambda i: "{:.2f}".format(i),
        }
        aligns = {
            'number': '>',
            'income': '>',
        }
        if header:
            data.append(tuple(Invoice.get_field_translation(field_name) for field_name in field_names))
        for invoice in invoice_collection:
            data.append(tuple(converters.get(field_name, str)(getattr(invoice, field_name)) for field_name in field_names))
        if data:
            lengths = [max(len(row[c]) for row in data) for c, f in enumerate(field_names)]
            fmt = " ".join("{{row[{i}]:{align}{{lengths[{i}]}}s}}".format(i=i, align=aligns.get(f, '<')) for i, f in enumerate(field_names))
            for row in data:
                self.print_function(fmt.format(row=row, lengths=lengths))

    def dump_invoice_collection(self, invoice_collection):
        invoice_collection.process()
        digits = 1 + int(math.log10(max(1, len(invoice_collection))))
        for invoice in invoice_collection:
            self.print_function("""\
fattura:                   {doc_filename!r}
  anno/numero:             {year}/{number:0{digits}d}
  città/data:              {city}/{date}
  nome:                    {name}
  codice fiscale:          {tax_code}
  importo:                 {income:.2f} [{currency}]""".format(digits=digits, **invoice._asdict()))

    def report_invoice_collection(self, invoice_collection):
        invoice_collection.process()
        for year in invoice_collection.years():
            year_invoices = invoice_collection.filter(lambda invoice: invoice.year == year)
            td = collections.OrderedDict()
            wd = collections.OrderedDict()
            for invoice in year_invoices:
                td.setdefault(invoice.tax_code, []).append(invoice)
                wd.setdefault(self.get_week_number(invoice.date), []).append(invoice)
            self.print_function("""\
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
                self.print_function("""\
    + cliente:             {tax_code} ({name}):
      numero di fatture:   {num_invoices}
      incasso totale:      {client_total_income:.2f}
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
            self.print_function("""\
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
                self.print_function("""\
    + settimana:           {week} [{first_date} -> {last_date}]:
      numero di fatture:   {num_invoices}
      incasso totale:      {week_total_income:.2f}
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
        

    def db_init(self, *, patterns, reset, partial_update=True, remove_orphaned=False):
        if reset and os.path.exists(self.db_filename):
            self.logger.info("cancellazione del db {!r}...".format(self.db_filename))
            os.remove(self.db_filename)
        self.db.initialize()
        self.db.configure(
            patterns=patterns,
            remove_orphaned=remove_orphaned,
            partial_update=partial_update,
        )
       

    def db_config(self, *, patterns, show, partial_update=True, remove_orphaned=False):
        new_patterns = []
        del_patterns = []
        for sign, pattern in patterns:
            if sign == '+':
                new_patterns.append(self.db.Pattern(pattern=Path.db_to(pattern)))
            elif sign == '-':
                del_patterns.append(self.db.Pattern(pattern=Path.db_to(pattern)))
        if new_patterns:
            self.db.write('patterns', new_patterns)
        if del_patterns:
            for pattern in del_patterns:
                self.db.delete('patterns', "pattern == {!r}".format(pattern.pattern))
        self.db.configure(
                patterns=None,
                remove_orphaned=remove_orphaned,
                partial_update=partial_update,
            )
        if show:
            self.db.show_configuration(print_function=self.print_function)

    def db_scan(self, *, warning_mode, error_mode, partial_update=True, remove_orphaned=False):
        self.db.check()
        validation_result, invoice_collection = self.scan(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )
        for doc_filename in validation_result.errors():
            print("   ", doc_filename)
        return validation_result, invoice_collection

    def db_clear(self):
        self.db.check()
        self.db.delete('invoices')

    def db_validate(self, *, warning_mode, error_mode):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
        self.validate_invoice_collection(validation_result, invoice_collection)
        return validation_result.num_errors()

    def db_filter(self, invoice_collection, filters):
        if filters:
            self.logger.debug("applicazione filtri su {} fatture...".format(len(invoice_collection)))
            for filter_source in filters:
                self.logger.debug("applicazione filtro {!r} su {} fatture...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        return invoice_collection

    def db_list(self, *, field_names=None, header=True, filters=None):
        if field_names is None:
            field_names = Invoice._fields
        if filters is None:
            filters = ()
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        self.list_invoice_collection(invoice_collection, header=header, field_names=field_names)

    def db_dump(self, *, filters=None):
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        self.dump_invoice_collection(invoice_collection)

    def db_report(self, *, filters=None):
        if filters is None:
            filters = ()
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        self.report_invoice_collection(invoice_collection)

    def legacy(self, patterns, filters, validate, list, report, warning_mode, error_mode):
        invoice_collection_reader = InvoiceCollectionReader(trace=self.trace)

        invoice_collection = invoice_collection_reader(*patterns)

        if validate is None:
            validate = any([report])

        try:
            if validate:
                self.logger.debug("validazione di {} fatture...".format(len(invoice_collection)))
                validation_result=self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
                validation_result = self.validate_invoice_collection(validation_result, invoice_collection)
                if validation_result.num_errors():
                    self.logger.error("trovati #{} errori!".format(validation_result.num_errors()))
                    return 1
    
            invoice_collection = self.db_filter(invoice_collection, filters)
    
            if list:
                self.logger.debug("lista di {} fatture...".format(len(invoice_collection)))
                self.dump_invoice_collection(invoice_collection)
    
            if report:
                self.logger.debug("report di {} fatture...".format(len(invoice_collection)))
                self.report_invoice_collection(invoice_collection)
    
        except Exception as err:
            if self.trace:
                traceback.print_exc()
            self.logger.error("{}: {}\n".format(type(err).__name__, err))

    def scan(self, warning_mode=None, error_mode=None, partial_update=None, remove_orphaned=None):
        found_doc_filenames = set()
        db = self.db
        file_date_times = FileDateTimes()
        updated_invoice_collection = InvoiceCollection()
        removed_doc_filenames = []
        with db.connect() as connection:
            configuration = db.load_configuration(connection)
            if remove_orphaned is None:
                remove_orphaned = configuration.remove_orphaned
            if partial_update is None:
                partial_update = configuration.partial_update

            for pattern in db.load_patterns(connection=connection):
                for doc_filename in glob.glob(pattern.pattern):
                    found_doc_filenames.add(Path.db_to(doc_filename))
            doc_filename_d = {}
            for scan_date_time in db.read('scan_date_times', connection=connection):
                doc_filename_d[scan_date_time.doc_filename] = scan_date_time.scan_date_time

            result = []
            scanned_doc_filenames = set()

            # update scanned invoices
            invoice_collection = db.load_invoice_collection()
            for invoice in invoice_collection:
                scanned_doc_filenames.add(invoice.doc_filename)
                to_remove = False
                if not os.path.exists(invoice.doc_filename):
                    to_update = False
                    if remove_orphaned:
                        to_remove = True
                elif not invoice.doc_filename in doc_filename_d:
                    to_update = True
                elif doc_filename_d[invoice.doc_filename] < file_date_times[invoice.doc_filename]:
                    to_update = True
                else:
                    to_update = False
                if to_remove:
                    removed_doc_filenames.append(invoice.doc_filename)
                else:
                    if to_update:
                        result.append((True, invoice.doc_filename))
                    else:
                        updated_invoice_collection.add(invoice)
          
            # unscanned invoices
            for doc_filename in found_doc_filenames.difference(scanned_doc_filenames):
                result.append((False, doc_filename))

            validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
            if result:
                invoice_reader = InvoiceReader(logger=self.logger)
                new_invoices = []
                old_invoices = []
                scan_date_times = []
                for existing, doc_filename in result:
                    try:
                        invoice = invoice_reader(doc_filename)
                    except Exception as err:
                        if self.trace:
                            traceback.print_exc()
                        self.logger.error("fattura {!r}: {}: {}".format(doc_filename, type(err).__name__, err))
                        continue
                    updated_invoice_collection.add(invoice_reader(doc_filename))
                    if existing:
                        old_invoices.append(invoice)
                    else:
                        new_invoices.append(invoice)
                    scan_date_times.append(db.ScanDateTime(doc_filename=invoice.doc_filename, scan_date_time=file_date_times[invoice.doc_filename]))
                self.validate_invoice_collection(validation_result, updated_invoice_collection)
                if validation_result.num_errors():
                    message = "validazione fallita - {} errori".format(validation_result.num_errors())
                    if not partial_update:
                        raise InvoiceValidationError(message)
                    else:
                        old_invoices = validation_result.filter_validated_invoices(old_invoices)
                        new_invoices = validation_result.filter_validated_invoices(new_invoices)
                        if old_invoices or new_invoices or removed_doc_filenames:
                            self.logger.warning(message + ' - update parziale')
                if old_invoices:
                    db.update('invoices', 'doc_filename', old_invoices, connection=connection)
                if new_invoices:
                    db.write('invoices', new_invoices, connection=connection)
                db.update('scan_date_times', 'doc_filename', scan_date_times, connection=connection)
            if removed_doc_filenames:
                for doc_filename in removed_doc_filenames:
                    db.delete('invoices', '''doc_filename == {!r}'''.format(doc_filename), connection=connection)
        return validation_result, updated_invoice_collection
