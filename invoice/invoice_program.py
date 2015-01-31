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
                   InvoiceValidationError, \
                   InvoicePartialUpdateError

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

    def __init__(self, db_filename, logger, printer=print, trace=False):
        self.db_filename = db_filename
        self.logger = logger
        self.printer = printer
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

    def program_help(self, *, parser_dict, command):
        parser = parser_dict[command]
        parser.print_help(file=self.printer.stream)
        return 0

    def program_missing_subcommand(self, *, parser):
        parser.print_help(file=self.printer.stream)
        self.logger.error("deve essere specificato un comando")
        return 1

    def program_version(self):
        self.impl_version()
        return 0

    def program_config(self, *, warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                                error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                                partial_update=True,
                                remove_orphaned=False,
                                reset=False):
        self.impl_config(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            reset=reset,
        )
        return 0

    def program_patterns(self, *, patterns=False, reset=False):
        self.impl_patterns(reset=reset, patterns=patterns)
        return 0

    def program_scan(self, *, warning_mode, error_mode, partial_update=True, remove_orphaned=False):
        validation_result, invoice_collection = self.impl_scan(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )
        if validation_result.num_errors():
            max_errors = 5
            self.logger.error("i primi {} errori sono:".format(max_errors))
            failing_invoices = InvoiceCollection(validation_result.filter_failing_invoices(invoice_collection))
            failing_invoices.process()
            for c, invoice in enumerate(failing_invoices):
                self.logger.error(" {:2d}) {!r}".format(c, invoice.doc_filename))
                errors = validation_result.errors().get(invoice.doc_filename, [])
                for error in errors:
                    self.logger.error(" {:2s}  {}".format('', error.message))
                if (c + 1) >= max_errors:
                    break
        return validation_result.num_errors()

    def program_clear(self):
        self.impl_clear()
        return 0

    def program_validate(self, *, warning_mode, error_mode):
        self.impl_validate(warning_mode=warning_mode, error_mode=error_mode)
        return 0

    def program_list(self, *, field_names=None, header=True, filters=None):
        self.impl_list(field_names=field_names, header=header, filters=filters)
        return 0

    def program_dump(self, *, filters=None):
        self.impl_dump(filters=filters)
        return 0

    def program_report(self, *, filters=None):
        self.impl_report(filters=filters)
        return 0

    def legacy(self, patterns, filters, validate, list, report, warning_mode, error_mode):
        self.impl_legacy(
            patterns=patterns,
            filters=filters,
            validate=validate,
            list=list,
            report=report,
            warning_mode=warning_mode,
            error_mode=error_mode,
        )
        return 0

    ## implementations:
    def show_configuration(self, configuration):
        self.printer("configuration:")
        for field_name in configuration._fields:
            self.printer("  + {:20s} = {!r}".format(field_name, getattr(configuration, field_name)))

    def show_patterns(self, patterns):
        self.printer("patterns:")
        for pattern in self.db.load_patterns():
            self.printer("  + {!r}".format(pattern))

    def check_patterns(self, patterns):
        non_patterns = self.db.non_patterns(patterns)
        if non_patterns:
            for pattern in non_patterns:
                self.logger.warning("pattern {!r}: non contiene wildcard: probabilmente hai dimenticato gli apici".format(pattern.pattern))

    def impl_init(self, *, patterns,
                           warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                           error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                           partial_update=True,
                           remove_orphaned=False,
                           reset=False):
        if reset and os.path.exists(self.db_filename):
            self.logger.info("cancellazione del db {!r}...".format(self.db_filename))
            os.remove(self.db_filename)
        self.db.initialize()
        configuration = self.db.Configuration(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )
        configuration = self.db.store_configuration(configuration)
        #self.show_configuration(configuration)
        self.check_patterns(patterns)
        patterns = self.db.store_patterns(patterns)
        #self.show_patterns(patterns)

       
    def impl_version(self):
        self.db.check()
        version = self.db.load_version()
        self.printer("versione del database:  {}.{}.{}".format(*version))
        self.printer("versione del programma: {}.{}.{}".format(*self.db.VERSION))

    def impl_config(self, *, warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                             error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                             partial_update=True,
                             remove_orphaned=False,
                             reset=False):
        self.db.check()
        if reset:
            self.db.clear('configuration')
        configuration = self.db.Configuration(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )
        configuration = self.db.store_configuration(configuration)
        self.show_configuration(configuration)


    def impl_patterns(self, *, reset, patterns, partial_update=True, remove_orphaned=False):
        if reset:
            self.db.clear('patterns')
        new_patterns = []
        del_patterns = []
        old_patterns = self.db.load_patterns()
        for sign, pattern in patterns:
            if sign == '+':
                new_patterns.append(pattern)
            elif sign == '-':
                del_patterns.append(pattern)
        if new_patterns:
            l = []
            for pattern in new_patterns:
                if pattern in old_patterns:
                    self.logger.warning("pattern {!r}: già definito".format(pattern))
                else:
                    l.append(pattern)
            new_patterns = l
            self.check_patterns(new_patterns)
            self.db.write('patterns', new_patterns)
        if del_patterns:
            self.check_patterns(del_patterns)
            for pattern in del_patterns:
                self.db.delete('patterns', "pattern == {!r}".format(pattern.pattern))
        self.show_patterns(patterns)

    def impl_clear(self):
        self.db.check()
        self.db.delete('invoices')

    def impl_validate(self, *, warning_mode, error_mode):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
        self.validate_invoice_collection(validation_result, invoice_collection)
        return validation_result.num_errors()

    def impl_list(self, *, field_names=None, header=True, filters=None):
        self.db.check()
        if field_names is None:
            field_names = Invoice._fields
        if filters is None:
            filters = ()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters)
        self.list_invoice_collection(invoice_collection, header=header, field_names=field_names)

    def impl_dump(self, *, filters=None):
        self.db.check()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters)
        self.dump_invoice_collection(invoice_collection)

    def impl_report(self, *, filters=None):
        self.db.check()
        if filters is None:
            filters = ()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters)
        self.report_invoice_collection(invoice_collection)

    def impl_legacy(self, patterns, filters, validate, list, report, warning_mode, error_mode):
        invoice_collection_reader = InvoiceCollectionReader(trace=self.trace)

        invoice_collection = invoice_collection_reader(*[pattern.pattern for pattern in patterns])

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
    
            invoice_collection = self.filter_invoice_collection(invoice_collection, filters)
    
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

    def impl_scan(self, warning_mode=None, error_mode=None, partial_update=None, remove_orphaned=None):
        self.db.check()
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
                scan_date_times = collections.OrderedDict()
                for existing, doc_filename in result:
                    try:
                        invoice = invoice_reader(doc_filename)
                    except Exception as err:
                        if self.trace:
                            traceback.print_exc()
                        self.logger.error("fattura {!r}: {}: {}".format(doc_filename, type(err).__name__, err))
                        continue
                    updated_invoice_collection.add(invoice)
                    if existing:
                        old_invoices.append(invoice)
                    else:
                        new_invoices.append(invoice)
                    scan_date_times[invoice.doc_filename] = db.ScanDateTime(
                        doc_filename=invoice.doc_filename,
                        scan_date_time=file_date_times[invoice.doc_filename])
                self.validate_invoice_collection(validation_result, updated_invoice_collection)
                if validation_result.num_errors():
                    message = "validazione fallita - {} errori".format(validation_result.num_errors())
                    if not partial_update:
                        raise InvoiceValidationError(message)
                    else:
                        old_invoices = validation_result.filter_validated_invoices(old_invoices)
                        new_invoices = validation_result.filter_validated_invoices(new_invoices)
                        #partially_updated_invoices = validation_result.filter_validated_invoices(updated_invoice_collection)
                        #partially_updated_invoice_collection = InvoiceCollection(partially_updated_invoices)
                        #partial_validation_result = self.create_validation_result()
                        #self.validate_invoice_collection(partial_validation_result, partially_updated_invoice_collection)
                        #if partial_validation_result.num_errors():
                        #    raise InvoicePartialUpdateError("validation of partial invoice collection failed")
                        if old_invoices or new_invoices or removed_doc_filenames:
                            self.logger.warning(message + ' - update parziale')
                scan_date_times_l = []
                if old_invoices:
                    db.update('invoices', 'doc_filename', old_invoices, connection=connection)
                    for invoice in old_invoices:
                        scan_date_times_l.append(scan_date_times[invoice.doc_filename])
                if new_invoices:
                    db.write('invoices', new_invoices, connection=connection)
                    for invoice in new_invoices:
                        scan_date_times_l.append(scan_date_times[invoice.doc_filename])
                db.update('scan_date_times', 'doc_filename', scan_date_times_l, connection=connection)
            if removed_doc_filenames:
                for doc_filename in removed_doc_filenames:
                    db.delete('invoices', '''doc_filename == {!r}'''.format(doc_filename), connection=connection)
        return validation_result, updated_invoice_collection

    ## functions
    def filter_invoice_collection(self, invoice_collection, filters):
        if filters:
            self.logger.debug("applicazione filtri su {} fatture...".format(len(invoice_collection)))
            for filter_source in filters:
                self.logger.debug("applicazione filtro {!r} su {} fatture...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        return invoice_collection

    def validate_invoice_collection(self, validation_result, invoice_collection):
        self.logger.debug("validation of {} invoices...".format(len(invoice_collection)))
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
            invoices = validation_result.filter_validated_invoices(invoice_collection.filter(lambda invoice: invoice.year == year))
            numbers = {}
            expected_number = 1
            prev_doc, prev_date = None, None
            for invoice in invoices:
                failed = False
                if invoice.number != expected_number:
                    if invoice.number in numbers:
                        validation_result.add_error(invoice, InvoiceDuplicatedNumberError,
                            "fattura {i}: il numero {y}/{n} è duplicato [presente anche in {l}]".format(
                                i=invoice.doc_filename,
                                y=year,
                                n=invoice.number,
                                l=', '.join("{}:{}".format(invoice.number, invoice.doc_filename) for invoice in numbers[invoice.number])))
                        failed = True
                    else:
                        validation_result.add_error(invoice, InvoiceWrongNumberError,
                            "fattura {i}: il numero {y}/{n} non è valido (il numero atteso è {e})".format(
                                i=invoice.doc_filename,
                                y=year,
                                n=invoice.number,
                                e=expected_number))
                        failed = True
                if prev_date is not None:
                    if invoice.date is not None and invoice.date < prev_date:
                        validation_result.add_error(invoice, InvoiceDateError, "fattura {}: la data {} precede quella della precedente fattura {} ({})".format(invoice.doc_filename, invoice.date, prev_doc, prev_date))
                        failed = True
                if not failed:
                    expected_number += 1
                    numbers.setdefault(invoice.number, []).append(invoice)
                    prev_doc, prev_date = invoice.doc_filename, invoice.date

        
        self.logger.debug("validation of {} invoices completed with {} errors and {} warnings".format(
            len(invoice_collection),
            validation_result.num_errors(),
            validation_result.num_warnings()))
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
                self.printer(fmt.format(row=row, lengths=lengths))

    def dump_invoice_collection(self, invoice_collection):
        invoice_collection.process()
        digits = 1 + int(math.log10(max(1, len(invoice_collection))))
        for invoice in invoice_collection:
            self.printer("""\
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
            self.printer("""\
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
                self.printer("""\
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
            self.printer("""\
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
                self.printer("""\
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
        

    def program_init(self, *, patterns,
                              warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                              error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                              partial_update=True,
                              remove_orphaned=False,
                              reset=False):
        self.impl_init(
            patterns=patterns,
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            reset=reset,
        )
        return 0
