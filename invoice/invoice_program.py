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

import calendar
import collections
import datetime
import fnmatch
import glob
import math
import os
import subprocess
import tempfile
import time
import traceback

from .error import InvoiceSyntaxError, \
                   InvoiceDateError, \
                   InvoiceMultipleNamesError, \
                   InvoiceMultipleTaxCodesError, \
                   InvoiceMultipleInvoicesPerDayError, \
                   InvoiceWrongNumberError, \
                   InvoiceDuplicatedNumberError, \
                   InvoiceMalformedTaxCodeError, \
                   InvoiceValidationError, \
                   InvoiceUserValidatorError, \
                   InvoiceArgumentError

from .info import load_info
from .invoice_collection import InvoiceCollection
from .invoice_collection_reader import InvoiceCollectionReader
from .invoice_reader import InvoiceReader
from .invoice_db import InvoiceDb
from .invoice import Invoice
from .spy import observe
from .spy import notify_osd
from .spy.spy_function import spy_function
from .validation_result import ValidationResult
from .week import WeekManager
from .database.db_types import Path
from .document import document, item_getter, Formats
from . import conf
from .scanner import load_scanner
from .parser import load_parser
from .version import VERSION
from .ee import snow


MReport = collections.namedtuple("MReport", ["number", "fee", "cpa", "taxable_income", "vat", "empty", "deduction", "income"])

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
    if observe.available():
        SPY_DAEMON_ACTIONS = tuple(observe.DocObserver.ACTIONS)
    else:
        SPY_DAEMON_ACTIONS = ()
    SPY_ACTION_RUN = 'run'
    SPY_ACTION_LOG = 'log'
    SPY_NON_DAEMON_ACTIONS = (SPY_ACTION_RUN, SPY_ACTION_LOG)
    SPY_ACTIONS = SPY_NON_DAEMON_ACTIONS + SPY_DAEMON_ACTIONS
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

    def program_help(self, *, parser_dict, argument):
        self.impl_help(parser_dict=parser_dict, argument=argument)
        return 0

    def program_missing_subcommand(self, *, parser):
        parser.print_help(file=self.printer.stream)
        self.logger.error("deve essere specificato un comando")
        return 1

    def program_version(self, upgrade=False):
        self.impl_version(upgrade=upgrade)
        return 0

    def program_init(self, *, patterns,
                              warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                              error_mode=ValidationResult.DEFAULT_ERROR_MODE,
                              partial_update=True,
                              remove_orphaned=False,
                              header=True,
                              total=True,
                              stats_group=None,
                              list_field_names=None,
                              show_scan_report=None,
                              table_mode=None,
                              max_interruption_days=None,
                              spy_notify_level=None,
                              spy_delay=None,
                              reset=False):
        self.impl_init(
            patterns=patterns,
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            header=header,
            total=total,
            list_field_names=list_field_names,
            stats_group=stats_group,
            show_scan_report=show_scan_report,
            table_mode=table_mode,
            max_interruption_days=max_interruption_days,
            spy_notify_level=spy_notify_level,
            spy_delay=spy_delay,
            reset=reset,
        )
        return 0

    def program_config(self, *, warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                                error_mode=ValidationResult.DEFAULT_ERROR_MODE,
                                partial_update=True,
                                remove_orphaned=True,
                                header=True,
                                total=True,
                                list_field_names=None,
                                stats_group=None,
                                show_scan_report=None,
                                table_mode=None,
                                max_interruption_days=None,
                                spy_notify_level=None,
                                spy_delay=None,
                                reset=False,
                                import_filename=None,
                                export_filename=None,
                                edit=False,
                                editor=None):
        self.impl_config(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            header=header,
            total=total,
            list_field_names=list_field_names,
            stats_group=stats_group,
            show_scan_report=show_scan_report,
            table_mode=table_mode,
            max_interruption_days=max_interruption_days,
            spy_notify_level=spy_notify_level,
            spy_delay=spy_delay,
            reset=reset,
            import_filename=import_filename,
            export_filename=export_filename,
            edit=edit,
            editor=editor,
        )
        return 0

    def program_patterns(self, *, patterns, reset=False, import_filename=None, export_filename=None, edit=False, editor=None):
        self.impl_patterns(
            reset=reset,
            patterns=patterns,
            import_filename=import_filename,
            export_filename=export_filename,
            edit=edit,
            editor=editor,
        )
        return 0

    def program_validators(self, *, validators, reset=False, import_filename=None, export_filename=None, edit=False, editor=None):
        self.impl_validators(
            reset=reset,
            validators=validators,
            import_filename=import_filename,
            export_filename=export_filename,
            edit=edit,
            editor=editor,
        )
        return 0

    def program_spy(self, *, action=None, spy_notify_level=None, spy_delay=None): # pragma: no cover
        self.impl_spy(action=action, spy_notify_level=spy_notify_level, spy_delay=spy_delay)
        return 0

    def program_scan(self, *, warning_mode, error_mode, force_refresh=None,
                              partial_update=True, remove_orphaned=True, show_scan_report=True, table_mode=None, output_filename=None):
        validation_result, scan_events, invoice_collection = self.impl_scan(
            warning_mode=warning_mode,
            error_mode=error_mode,
            force_refresh=force_refresh,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            show_scan_report=show_scan_report,
            table_mode=table_mode,
            output_filename=output_filename,
        )
        return validation_result.num_errors()

    def program_clear(self):
        self.impl_clear()
        return 0

    def program_validate(self, *, warning_mode, error_mode):
        self.impl_validate(warning_mode=warning_mode, error_mode=error_mode)
        return 0

    def program_list(self, *, list_field_names=None, header=None, filters=None, date_from=None, date_to=None, order_field_names=None, table_mode=None, output_filename=None):
        self.impl_list(list_field_names=list_field_names, header=header,
            filters=filters, date_from=date_from, date_to=date_to,
            order_field_names=order_field_names,
            table_mode=table_mode,
            output_filename=output_filename)
        return 0

    def program_dump(self, *, filters=None, date_from=None, date_to=None):
        self.impl_dump(filters=filters, date_from=date_from, date_to=date_to)
        return 0

    def program_report(self, *, filters=None):
        self.impl_report(filters=filters)
        return 0

    def program_summary(self, *, year=None, table_mode=None, output_filename=None, header=None):
        self.impl_summary(year=year, table_mode=table_mode, output_filename=output_filename, header=header)
        return 0

    def program_stats(self, *, filters=None, date_from=None, date_to=None, stats_group=None, total=None, stats_mode=None, header=None, table_mode=None, output_filename=None):
        self.impl_stats(filters=filters, date_from=date_from, date_to=date_to, stats_group=stats_group, total=total, stats_mode=stats_mode, header=header, table_mode=table_mode,
            output_filename=output_filename)
        return 0

    def legacy(self, patterns, filters, date_from, date_to, validate, list, report, warning_mode, error_mode):
        self.impl_legacy(
            patterns=patterns,
            filters=filters,
            date_from=date_from,
            date_to=date_to,
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
            self.printer("  + {:24s} = {!r}".format(field_name, getattr(configuration, field_name)))

    def show_patterns(self, patterns):
        self.printer("patterns:")
        for pattern in self.db.load_patterns():
            self.printer("  + {!r}".format(pattern))

    def show_validators(self):
        self.printer("validators:")
        for validator in self.db.load_validators():
            self.printer("  + filter:  {!r}".format(validator.filter_function))
            self.printer("    check:   {!r}".format(validator.check_function))
            self.printer("    message: {!r}".format(validator.message))

    def check_patterns(self, patterns):
        non_patterns = self.db.non_patterns(patterns)
        if non_patterns:
            for pattern in non_patterns:
                self.logger.warning("pattern {!r}: non contiene wildcard: probabilmente hai dimenticato gli apici".format(pattern.pattern))

    def edit(self, filename, editor=None):
        if editor is None: # pragma: no cover
            editor = conf.DEFAULT_EDITOR
        cmdline = "{} {}".format(editor, filename)
        with subprocess.Popen([cmdline], shell=True) as p:
            pass

    def edit_table(self, table_name, editor=None, connection=None):
        with self.db.connect(connection) as connection, tempfile.NamedTemporaryFile() as t_file:
            t_filename = t_file.name
            self.db.export_table(table_name, t_filename, connection=connection)
            t_file.flush()
            self.edit(filename=t_filename, editor=editor)
            t_file.flush()
            self.db.clear(table_name, connection=connection)
            self.db.import_table(table_name, t_filename, connection=connection)

    def impl_init(self, *, patterns,
                           warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                           error_mode=ValidationResult.DEFAULT_ERROR_MODE,
                           partial_update=True,
                           remove_orphaned=True,
                           header=True,
                           total=True,
                           stats_group=None,
                           list_field_names=None,
                           show_scan_report=None,
                           table_mode=None,
                           max_interruption_days=None,
                           spy_notify_level=None,
                           spy_delay=None,
                           reset=False):
        if list_field_names is None:
            lsit_field_names = conf.DEFAULT_LIST_FIELD_NAMES
        scanner_config_file = conf.get_scanner_config_file()
        parser_config_file = conf.get_parser_config_file()
        if reset:
            if os.path.exists(self.db_filename):
                self.logger.info("cancellazione del db {!r}...".format(self.db_filename))
                os.remove(self.db_filename)
            if os.path.exists(scanner_config_file):
                self.logger.info("cancellazione dello scanner config file {!r}...".format(scanner_config_file))
                os.remove(scanner_config_file)
            if os.path.exists(parser_config_file):
                self.logger.info("cancellazione del parser config file {!r}...".format(parser_config_file))
                os.remove(parser_config_file)
        self.db.initialize()
        configuration = self.db.Configuration(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            header=header,
            total=total,
            list_field_names=list_field_names,
            stats_group=stats_group,
            show_scan_report=show_scan_report,
            table_mode=table_mode,
            max_interruption_days=max_interruption_days,
            spy_notify_level=spy_notify_level,
            spy_delay=spy_delay,
        )
        configuration = self.db.store_configuration(configuration)
        #self.show_configuration(configuration)
        self.check_patterns(patterns)
        patterns = self.db.store_patterns(patterns)
        #self.show_patterns(patterns)
        load_scanner(scanner_config_file)
        load_parser(parser_config_file)

       
    def impl_version(self, upgrade=False):
        self.db.check_existence()
        self.printer("versione del programma: {}.{}.{}".format(*VERSION))
        if upgrade:
            version = self.db.load_version()
            self.printer("versione del database:  {}.{}.{}".format(*version))
            self.printer("upgrade...")
            self.db.upgrade()
        version = self.db.load_version()
        self.printer("versione del database:  {}.{}.{}".format(*version))
        if not self.db.version_is_valid(version):
            self.logger.error("la versione del database non è valida; è necessario eseguire l'upgrade (opzione --upgrade/-U)")

    def impl_config(self, *, warning_mode=ValidationResult.DEFAULT_WARNING_MODE,
                             error_mode=ValidationResult.DEFAULT_ERROR_MODE,
                             partial_update=True,
                             remove_orphaned=True,
                             header=True,
                             total=True,
                             list_field_names=None,
                             stats_group=None,
                             show_scan_report=None,
                             table_mode=None,
                             max_interruption_days=None,
                             spy_notify_level=None,
                             spy_delay=None,
                             reset=False,
                             import_filename=None,
                             export_filename=None,
                             edit=False,
                             editor=None):
        self.db.check()
        if reset:
            self.db.clear('configuration')
        if import_filename:
            self.db.import_table('configuration', import_filename)
        list_field_names = self.db.get_config_option('list_field_names', list_field_names)
        if error_mode is not None:
            error_mode = tuple(error_mode)
        if warning_mode is not None:
            warning_mode = tuple(warning_mode)
        configuration = self.db.Configuration(
            warning_mode=warning_mode,
            error_mode=error_mode,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
            header=header,
            total=total,
            list_field_names=list_field_names,
            stats_group=stats_group,
            show_scan_report=show_scan_report,
            table_mode=table_mode,
            max_interruption_days=max_interruption_days,
            spy_notify_level=spy_notify_level,
            spy_delay=spy_delay,
        )
        configuration = self.db.store_configuration(configuration)
        if edit:
            self.edit_table(table_name='configuration', editor=editor)
            configuration = self.db.load_configuration()
        self.show_configuration(configuration)
        if export_filename:
            self.db.export_table('configuration', export_filename)


    def impl_patterns(self, *, reset, patterns, import_filename=None, export_filename=None, edit=False, editor=None):
        self.db.check()
        if reset:
            self.db.clear('patterns')
        if import_filename:
            self.db.import_table('patterns', import_filename)
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
        if edit:
            self.edit_table(table_name='patterns', editor=editor)
            patterns = self.db.load_patterns()
        self.show_patterns(patterns)
        if export_filename:
            self.db.export_table('patterns', export_filename)

    def impl_validators(self, *, reset, validators, import_filename=None, export_filename=None, edit=False, editor=None):
        self.db.check()
        if reset:
            self.db.clear('validators')
        if import_filename:
            self.db.import_table('validators', import_filename)
        vlist = []
        for filter_function, check_function, message in validators:
            vlist.append(self.db.make_validator(filter_function=filter_function, check_function=check_function, message=message))
        self.db.write('validators', vlist)
        if edit:
            self.edit_table(table_name='validators', editor=editor)
        self.show_validators()
        if export_filename:
            self.db.export_table('validators', export_filename)

    def impl_clear(self):
        self.db.check()
        self.db.delete('invoices')

    def impl_validate(self, *, warning_mode, error_mode):
        self.db.check()
        warning_mode = self.db.get_config_option('warning_mode', warning_mode)
        error_mode = self.db.get_config_option('error_mode', error_mode)
        invoice_collection = self.db.load_invoice_collection()
        validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
        with self.db.connect() as connection:
            user_validators = self.compile_user_validators(connection)
            self.validate_invoice_collection(validation_result, invoice_collection, user_validators=user_validators)
            self.delete_failing_invoices(validation_result, connection=connection)
        return validation_result.num_errors()

    def impl_list(self, *, list_field_names=None, header=None, filters=None, date_from=None, date_to=None, order_field_names=None, table_mode=None, output_filename=None):
        self.db.check()
        if filters is None: # pragma: no cover
            filters = ()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters=filters, date_from=date_from, date_to=date_to)
        self.list_invoice_collection(invoice_collection, header=header, list_field_names=list_field_names, order_field_names=order_field_names, table_mode=table_mode,
            output_filename=output_filename)

    def impl_dump(self, *, filters=None, date_from=None, date_to=None):
        self.db.check()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters=filters, date_from=date_from, date_to=date_to)
        self.dump_invoice_collection(invoice_collection)

    def impl_report(self, *, filters=None):
        self.db.check()
        if filters is None:
            filters = ()
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters=filters)
        self.report_invoice_collection(invoice_collection)

    def impl_summary(self, *, year=None, table_mode=None, output_filename=None, header=None):
        table_mode = self.db.get_config_option('table_mode', table_mode)
        header = self.db.get_config_option('header', table_mode)
        self.db.check()
        filters = []
        if year is None:
            year = datetime.datetime.now().year
        filters.append(lambda i: i.year == year)
        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters=filters)
        
        all_field_names = MReport._fields

        #"number", "fee", "cpa", "taxable_income", "vat", "empty", "deduction", "income"
        header = ["N.DOC.", "COMPENSO", "C.P.A.", "IMPONIBILE IVA", "IVA 22%", "ES.IVA ART.10", "R.A.", "TOTALE"]
        total_keys = 'fee', 'cpa', 'taxable_income', 'vat', 'deduction', 'income'

        general_info = load_info()['general']
        summary_prologue = general_info['summary_prologue']
        summary_epilogue = general_info['summary_epilogue']

        with document(file=self.get_doc_file(output_filename), mode=table_mode, logger=self.logger) as doc:
            doc.define_format("bold", {"bold": True})
            doc.define_format("bold_yellow", {"bold": True, "bg_color": "yellow"})
            page_template = doc.create_page_template(field_names=all_field_names, header=header)
            for month in range(1, 12 + 1):
                m_filter = lambda i: i.date.month == month
                invoices = self.filter_invoice_collection(invoice_collection, filters=[m_filter])
                rows = []
                month_name = conf.MONTH_TRANSLATION[month - 1]
                prologue = None
                epilogue = None
                row_offset = 0
                doc_formats = Formats()
                if table_mode == conf.TABLE_MODE_XLSX:
                    prologue = []
                    if summary_prologue:
                        for line in summary_prologue.split('\n'):
                            prologue.append((line,))
                            doc_formats.add_format("bold", row=len(prologue) - 1, col=None)
                        prologue.append(('',))
                    prologue.append(('mese:', month_name))
                    doc_formats.add_format("bold_yellow", row=len(prologue) - 1, col=None)
                    prologue.append(('',))
                    row_offset += len(prologue)
                total = {}
                for key in total_keys:
                    total[key] = 0.0
                for invoice in invoices:
                    mreport = MReport(
                        number=invoice.number,
                        fee=invoice.fee,
                        cpa=invoice.cpa,
                        taxable_income=invoice.fee + invoice.cpa,
                        vat=invoice.vat,
                        empty="",
                        deduction=invoice.deduction,
                        income=invoice.income,
                    )
                    rows.append(mreport)
                    for key in total_keys:
                        val = getattr(mreport, key)
                        if val is not None:
                            total[key] += val
                total["number"] = "TOTALE"
                total["empty"] = ""
                if table_mode == conf.TABLE_MODE_XLSX:
                    separator = {key: "" for key in MReport._fields}
                    rows.append(MReport(**separator))
                rows.append(MReport(**total))
    
                doc_formats.add_format("bold", row=0 + row_offset, col=None)
                doc_formats.add_format("bold", row=None, col=0)
                num_rows = row_offset + len(rows)
                if header:
                    num_rows += 1
                doc_formats.add_format("bold_yellow", row=num_rows - 1, col=None)
                if table_mode == conf.TABLE_MODE_XLSX:
                    if summary_epilogue:
                        epilogue = []
                        epilogue.insert(0, ('',))
                        for line in summary_epilogue.split('\n'):
                            epilogue.append((line,))
                            doc_formats.add_format("bold", row=num_rows + len(epilogue) - 1, col=None)
                doc.add_page(page_template=page_template, data=rows, title=month_name, formats=doc_formats, prologue=prologue, epilogue=epilogue)

    def _get_year_group_value(self, invoices, year):
        return (year,
                datetime.date(year, 1, 1),
                datetime.date(year, 12, 31))

    def _get_month_group_value(self, invoices, year, month):
        date_from = datetime.date(year, month, 1)
        date_to = datetime.date(year, month, calendar.monthrange(year, month)[1])
        return (date_from.strftime("%Y-%m"),
                date_from,
                date_to)

    def _get_week_group_value(self, invoices, year, week_number):
        date_from, date_to = self.get_week_range(year, week_number)
        return ("{:4d}:{:02d}".format(year, week_number),
                date_from,
                date_to)

    def _get_day_group_value(self, invoices, date):
        return (date,
                date,
                date)

    def _get_weekday_group_value(self, invoices, weekday):
        return (conf.WEEKDAY_TRANSLATION[weekday],
                invoices[0].date,
                invoices[-1].date)

    def _get_group_value(self, invoices, value):
        return (value,
                invoices[0].date,
                invoices[-1].date)

    def _get_task_group_value(self, invoices, tax_code, name, service):
        return ((tax_code, name, service),
                invoices[0].date,
                invoices[-1].date)

    def group_by(self, invoice_collection, stats_group):
        invoice_collection.sort()
        invoices = invoice_collection
        if stats_group == conf.STATS_GROUP_YEAR:
            group_function = lambda invoice: (invoice.year, )
            group_value_function = self._get_year_group_value
        elif stats_group == conf.STATS_GROUP_MONTH:
            group_function = lambda invoice: (invoice.year, invoice.date.month)
            group_value_function = self._get_month_group_value
        elif stats_group == conf.STATS_GROUP_WEEK:
            group_function = lambda invoice: (invoice.year, self.get_week_number(invoice.date))
            group_value_function = self._get_week_group_value
        elif stats_group == conf.STATS_GROUP_DAY:
            group_function = lambda invoice: (invoice.date, )
            group_value_function = self._get_day_group_value
        elif stats_group == conf.STATS_GROUP_WEEKDAY:
            invoices = sorted(invoice_collection, key=lambda invoice: invoice.date.weekday())
            group_function = lambda invoice: (invoice.date.weekday(), )
            group_value_function = self._get_weekday_group_value
        elif stats_group == conf.STATS_GROUP_SERVICE:
            invoices = sorted(invoice_collection, key=lambda invoice: invoice.service)
            group_function = lambda invoice: (invoice.service, )
            group_value_function = self._get_group_value
        elif stats_group == conf.STATS_GROUP_TASK:
            invoices = sorted(invoice_collection, key=lambda invoice: (invoice.tax_code, invoice.name, invoice.service))
            group_function = lambda invoice: (invoice.tax_code, invoice.name, invoice.service, )
            group_value_function = self._get_task_group_value
        elif stats_group == conf.STATS_GROUP_CLIENT:
            invoices = sorted(invoice_collection, key=lambda invoice: invoice.tax_code)
            group_function = lambda invoice: (invoice.tax_code, )
            group_value_function = self._get_group_value
        elif stats_group == conf.STATS_GROUP_CITY:
            invoices = sorted(invoice_collection, key=lambda invoice: invoice.city)
            group_function = lambda invoice: (invoice.city, )
            group_value_function = self._get_group_value
        group_value = None
        group = []
        for invoice in invoices:
            value = group_function(invoice)
            if group_value is None:
                group_value = value
            if value != group_value:
                yield group_value_function(group, *group_value), tuple(group)
                del group[:]
                group_value = value
            group.append(invoice)
        if group:
            yield group_value_function(group, *group_value), group
   
    def impl_stats(self, *, filters=None, date_from=None, date_to=None, stats_group=None, total=None, stats_mode=None, header=None, table_mode=None, output_filename=None):
        total = self.db.get_config_option('total', total)
        header = self.db.get_config_option('header', header)
        table_mode = self.db.get_config_option('table_mode', table_mode)
        self.db.check()
        if filters is None: # pragma: no cover
            filters = ()

        if stats_group is None:
            stats_group = conf.DEFAULT_STATS_GROUP

        if stats_mode is None:
            stats_mode = conf.DEFAULT_STATS_MODE

        global_invoice_collection = self.db.load_invoice_collection()
        invoice_collection = self.filter_invoice_collection(global_invoice_collection, filters=filters, date_from=date_from, date_to=date_to)
        invoice_collection.sort()
        if invoice_collection:
            group_translation = {
                conf.STATS_GROUP_YEAR:		'anno',
                conf.STATS_GROUP_MONTH:		'mese',
                conf.STATS_GROUP_WEEK:		'settimana',
                conf.STATS_GROUP_DAY:		'giorno',
                conf.STATS_GROUP_WEEKDAY:	'giorno',
                conf.STATS_GROUP_CLIENT:	Invoice.get_field_translation('tax_code'),
                conf.STATS_GROUP_SERVICE:	Invoice.get_field_translation('service'),
                conf.STATS_GROUP_TASK:		'incarico',
                'name':                         Invoice.get_field_translation('name'),
                conf.STATS_GROUP_CITY:		Invoice.get_field_translation('city'),
                'from':				'da:',
                'to':				'a:',
            }
            convert = {
                'income': lambda income: '{:.2f}'.format(income),
                'income_percentage': lambda income_percentage: '{:.2%}'.format(income_percentage),
            }
            align = {
                'client_count': '>',
                'invoice_count': '>',
                'income': '>',
                'income_percentage': '>',
                'from': '>',
                'to': '>',
            }
            if stats_group == conf.STATS_GROUP_CLIENT:
                cc_field_name = 'name'
                cc_header = Invoice.get_field_translation(cc_field_name)
                cc_total = '--'
            else:
                cc_field_name = 'client_count'
                cc_header = 'clienti'
                cc_total = 0
            header_d = {
                'continuation':			'cont.',
                cc_field_name:			cc_header,
                'invoice_count':		'fatture',
                'income':			'incasso',
                'income_percentage':		'%incasso',
                'income_bar':			'h(incasso)',
                'invoice_count_bar':		'h(fatture)',
            }
            if stats_group == conf.STATS_GROUP_TASK:
                field_names = ()
            elif stats_group == conf.STATS_GROUP_CLIENT:
                field_names = (cc_field_name, 'continuation')
            else:
                field_names = (cc_field_name, )
            if stats_group == conf.STATS_GROUP_TASK:
                stats_group_fields = ('client', 'name', 'service')
            else:
                stats_group_fields = (stats_group, )
            if stats_mode == conf.STATS_MODE_SHORT:
                group_field_names = stats_group_fields
                field_names += ('invoice_count', 'income', 'income_percentage')
            elif stats_mode == conf.STATS_MODE_LONG:
                group_field_names = stats_group_fields + ('from', 'to')
                field_names += ('invoice_count', 'income', 'income_percentage')
            elif stats_mode == conf.STATS_MODE_FULL:
                group_field_names = stats_group_fields + ('from', 'to')
                field_names += ('invoice_count', 'invoice_count_bar', 'income', 'income_percentage', 'income_bar')
            cum_field_names = ('invoice_count', 'income', 'income_percentage')
            if header:
                field_header = tuple(header_d.get(field_name, field_name) for field_name in field_names)
                group_total = ('TOTAL', '', '')
                group_header = tuple(group_translation[field_name] for field_name in group_field_names)
                header = group_header + field_header
            all_field_names = group_field_names + field_names
            first_invoice = invoice_collection[0]
            last_invoice = invoice_collection[-1]
            first_date = first_invoice.date
            last_date = last_invoice.date
            total_income = sum(invoice.income for invoice in invoice_collection)
            total_invoice_count = len(invoice_collection)
            def bar(value, max_value, length=10, block='#', empty=' '):
                if max_value == 0: 
                    block_length, empty_length = 0, length
                else:
                    block_length = int(round(value * length / max_value, 0))
                    empty_length = length - block_length
                return (block * block_length) + (empty * empty_length)
            rows = []
            if total:
                total_row = {field_name: 0 for field_name in cum_field_names}
                total_s = "TOTALE"
                if stats_group == conf.STATS_GROUP_TASK:
                    total_row['client'] = total_s
                    total_row['name'] = ""
                    total_row['service'] = ""
                else:
                    total_row[stats_group] = total_s
                total_row['continuation'] = "--"
                total_row[cc_field_name] = cc_total
                total_row['from'] = ""
                total_row['to'] = ""
                total_row['income_bar'] = "--"
                total_row['invoice_count_bar'] = "--"
            total_client_count = len(set(invoice.tax_code for invoice in invoice_collection))
            configuration = self.db.load_configuration()
            year = datetime.timedelta(days=configuration.max_interruption_days)
            pre_post_symbol = {
                True:  {
                         True:  '<--->',
                         False: '<---]',
                       },
                False: {
                         True:  '[--->',
                         False: '[---]',
                       },
            }
            for (group_value, group_date_from, group_date_to), group in self.group_by(invoice_collection, stats_group):
                if date_from is not None and group_date_from is not None:
                    group_date_from = max(group_date_from, date_from)
                if date_to is not None and group_date_to is not None:
                    group_date_to = min(group_date_to, date_to)
                income = sum(invoice.income for invoice in group)
                if total_income != 0.0:
                    income_percentage = income / total_income
                else:
                    income_percentage = 0.0
                clients = set(invoice.tax_code for invoice in group)
                data = {
                    'stats_group':		group_translation[stats_group],
                    'invoice_count':		len(group),
                    'client_count':		len(clients),
                    'income':			income,
                    'income_percentage':	income_percentage,
                    'income_bar':		None,
                    'invoice_count_bar':	None,
                    stats_group:		group_value,
                    'from':			group_date_from,
                    'to':			group_date_to,
                }
                if stats_group == conf.STATS_GROUP_CLIENT:
                    continuation = None
                    pre_filters = [
                        lambda i: (i.tax_code == group_value) and (i.date < group_date_from and i.date >= group_date_from - year),
                    ]
                    pre_collection = self.filter_invoice_collection(global_invoice_collection, filters=pre_filters)
                    pre = len(pre_collection) > 0
                        
                    post_filters = [
                        lambda i: (i.tax_code == group_value) and (i.date > group_date_to and i.date <= group_date_to + year),
                    ]
                    post_collection = self.filter_invoice_collection(global_invoice_collection, filters=post_filters)
                    post = len(post_collection) > 0

                    data['continuation'] = pre_post_symbol[pre][post]
                if total:
                    for field_name in cum_field_names:
                        total_row[field_name] += data[field_name]
                    total_row['client_count'] = total_client_count
                if stats_group == conf.STATS_GROUP_CLIENT:
                    data[cc_field_name] = group[0].name
                elif stats_group == conf.STATS_GROUP_TASK:
                    data['client'] = group[0].tax_code
                    data['name'] = group[0].name
                    data['service'] = group[0].service
                rows.append(data)
            #bars
            max_income = max(row['income'] for row in rows)
            for row in rows:
                row['income_bar'] = bar(row['income'], max_income)
            max_invoice_count = max(row['invoice_count'] for row in rows)
            for row in rows:
                row['invoice_count_bar'] = bar(row['invoice_count'], max_invoice_count)
            if total:
                rows.append(total_row)
            with document(file=self.get_doc_file(output_filename), mode=table_mode, logger=self.logger) as doc:
                page_template = doc.create_page_template(
                    field_names=all_field_names,
                    header=header,
                    align=align,
                    convert=convert,
                    getter=item_getter)
                doc.add_page(page_template, rows)

    def impl_legacy(self, patterns, filters, date_from, date_to, validate, list, report, warning_mode, error_mode):
        invoice_collection_reader = InvoiceCollectionReader(trace=self.trace, logger=self.logger)

        validation_result=self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
        invoice_collection = invoice_collection_reader(validation_result, *[pattern.pattern for pattern in patterns])
        

        if validate is None:
            validate = any([report])

        try:
            if validate:
                self.logger.debug("validazione di {} fatture...".format(len(invoice_collection)))
                validation_result = self.validate_invoice_collection(validation_result, invoice_collection)
                if validation_result.num_errors():
                    self.logger.error("trovati #{} errori!".format(validation_result.num_errors()))
                    return 1
    
            invoice_collection = self.filter_invoice_collection(invoice_collection, filters=filters, date_from=date_from, date_to=date_to)
    
            if list:
                self.logger.debug("lista di {} fatture...".format(len(invoice_collection)))
                self.dump_invoice_collection(invoice_collection)
    
            if report:
                self.logger.debug("report di {} fatture...".format(len(invoice_collection)))
                self.report_invoice_collection(invoice_collection)
    
        except Exception as err: # pragma: no cover
            if self.trace:
                traceback.print_exc()
            self.logger.error("{}: {}\n".format(type(err).__name__, err))

    def compile_user_validators(self, connection=None):
        user_validators = []
        with self.db.connect() as connection:
            # validators
            for validator in self.db.load_validators(connection=connection):
                user_validators.append((validator, self.db.Validator(
                    Invoice.compile_filter_function(validator.filter_function),
                    Invoice.compile_filter_function(validator.check_function),
                    validator.message)))
        return user_validators
    
    def impl_spy(self, *, action=None, spy_notify_level=None, spy_delay=None): # pragma: no cover
        if not observe.available():
            raise NotImplementedError("funzione non disponibile; probabilmente devi installare watchdog ('sudo pip3 install watchdog')")
        if not notify_osd.available():
            raise NotImplementedError("funzione non disponibile; probabilmente devi installare python3-notify2 ('sudo apt-get install python3-notify2')")
        self.db.check()
        spy_delay = self.db.get_config_option('spy_delay', spy_delay)
        dirdata = {}
        for pattern in self.db.load_patterns():
            p_dirname, p_filename = os.path.split(pattern.pattern)
            for dirname in glob.glob(p_dirname):
                dirdata.setdefault(dirname, []).append(p_filename)

        function = lambda event_queue, spy_notify_level: spy_function(program=self, event_queue=event_queue, spy_notify_level=spy_notify_level)
        doc_observer = observe.DocObserver(dirdata=dirdata,
                                   function=function,
                                   logger=self.logger,
                                   spy_delay=spy_delay,
                                   spy_notify_level=spy_notify_level)
        if action == self.SPY_ACTION_RUN:
            doc_observer.run()
        elif action == self.SPY_ACTION_LOG:
            doc_observer.show_log(printer=self.printer)
        else:
            result = doc_observer.apply_action(action)
            self.printer("spy {} -> {}".format(action, result))
        
    def impl_scan(self, warning_mode=None, error_mode=None, force_refresh=None,
                        partial_update=None, remove_orphaned=None, show_scan_report=None, table_mode=None, output_filename=None):
        self.db.check()
        warning_mode = self.db.get_config_option('warning_mode', warning_mode)
        error_mode = self.db.get_config_option('error_mode', error_mode)
        show_scan_report = self.db.get_config_option('show_scan_report', show_scan_report)
        internal_options = self.db.load_internal_options()
        force_refresh = force_refresh or internal_options.needs_refresh
        found_doc_filenames = set()
        db = self.db
        file_date_times = FileDateTimes()
        updated_invoice_collection = InvoiceCollection()
        removed_invoices = []
        validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
        scan_events = {'removed': 0, 'added': 0, 'modified': 0}
        with db.connect() as connection:
            configuration = db.load_configuration(connection)
            user_validators = self.compile_user_validators(connection)
            if remove_orphaned is None:
                remove_orphaned = configuration.remove_orphaned
            if partial_update is None:
                partial_update = configuration.partial_update

            for pattern in db.load_patterns(connection=connection):
                if pattern.skip:
                    found_doc_filenames.difference_update(fnmatch.filter(found_doc_filenames, pattern.pattern))
                else:
                    for doc_filename in glob.glob(pattern.pattern):
                        found_doc_filenames.add(Path.db_to(doc_filename))
            doc_filename_d = {}
            for scan_date_time in db.read('scan_date_times', connection=connection):
                doc_filename_d[scan_date_time.doc_filename] = scan_date_time.scan_date_time

            existing_doc_filenames = collections.OrderedDict()
            scanned_doc_filenames = set()

            # update scanned invoices
            invoice_collection = db.load_invoice_collection(connection=connection)
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
                    removed_invoices.append(invoice)
                else:
                    if to_update:
                        existing_doc_filenames[invoice.doc_filename] = True
                    else:
                        updated_invoice_collection.add(invoice)
          
            if removed_invoices:
                discarded_doc_filenames = set()
                year_min_numbers = {}
                for invoice in removed_invoices:
                    self.logger.warning("fattura {f}: il documento {y}/{n} è stato rimosso".format(
                        f=invoice.doc_filename,
                        y=invoice.year,
                        n=invoice.number,
                    ))
                    year_min_numbers.setdefault(invoice.year, []).append(invoice.number)
                year_min_number = {year: min(min_numbers) for year, min_numbers in year_min_numbers.items()}
                for year, min_number in year_min_number.items():
                    self.logger.debug("tutte le fatture dell'anno {y} con numero >= {n} verranno rimosse dal database)".format(
                        y=year,
                        n=min_number,
                    ))
                    where = ['year == {}'.format(year), 'number >= {}'.format(min_number)]
                    for invoice in db.read('invoices', where=where, connection=connection):
                        discarded_doc_filenames.add(invoice.doc_filename)
                    db.delete('invoices', where=where, connection=connection)
                scan_events['removed'] += len(discarded_doc_filenames)
                # force rescan
                for doc_filename in discarded_doc_filenames:
                    existing_doc_filenames[doc_filename] = False

            # unscanned invoices
            for doc_filename in found_doc_filenames.difference(scanned_doc_filenames):
                existing_doc_filenames[doc_filename] = False

            for invoice in removed_invoices:
                existing_doc_filenames.pop(invoice.doc_filename)

            if existing_doc_filenames:
                invoice_reader = InvoiceReader(logger=self.logger)
                new_invoices = []
                old_invoices = []
                scan_date_times = collections.OrderedDict()
                for doc_filename, existing in existing_doc_filenames.items():
                    invoice = invoice_reader(validation_result, doc_filename)
                    updated_invoice_collection.add(invoice)
                    if existing:
                        old_invoices.append(invoice)
                        scan_events['modified'] += 1
                    else:
                        new_invoices.append(invoice)
                        scan_events['added'] += 1
                    scan_date_times[invoice.doc_filename] = db.ScanDateTime(
                        doc_filename=invoice.doc_filename,
                        scan_date_time=file_date_times[invoice.doc_filename])
                self.validate_invoice_collection(validation_result, updated_invoice_collection, user_validators=user_validators)
                if validation_result.num_errors():
                    message = "validazione fallita - {} errori".format(validation_result.num_errors())
                    if not partial_update:
                        raise InvoiceValidationError(message)
                    else:
                        old_invoices = validation_result.filter_validated_invoices(old_invoices)
                        new_invoices = validation_result.filter_validated_invoices(new_invoices)
                        if old_invoices or new_invoices:
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
            self.delete_failing_invoices(validation_result, connection=connection)
                    
            if validation_result.num_errors():
                failing_invoices = InvoiceCollection(validation_result.failing_invoices().values())
                failing_invoices.sort()
                max_errors = min(5, len(failing_invoices))
                self.logger.error("=" * 72)
                if max_errors > 0:
                    if max_errors == 1:
                        self.logger.error("la prima fattura contenente errori è:")
                    else:
                        self.logger.error("le prime {} fatture contenenti errori sono:".format(max_errors))
                    failing_invoices.sort()
                    for c, invoice in enumerate(failing_invoices):
                        self.logger.error(" {:2d}) {!r}".format(c, invoice.doc_filename))
                        errors = validation_result.errors().get(invoice.doc_filename, [])
                        for error in errors:
                            self.logger.error(" {:2s}  {}".format('', error.message))
                        if (c + 1) >= max_errors:
                            break

            if show_scan_report:
                invoice_collection = self.db.load_invoice_collection()
                invoice_collection.sort()
                last_invoice_of_the_year = collections.OrderedDict()
                for invoice in invoice_collection:
                    last_invoice_of_the_year[invoice.year] = invoice
                if validation_result.num_errors():
                    self.printer("")
                self.printer("#fatture aggiunte: {}".format(scan_events['added']))
                self.printer("#fatture modificate: {}".format(scan_events['modified']))
                self.printer("#fatture rimosse: {}".format(scan_events['removed']))
                self.printer("ultima fattura inserita per ciascun anno:")
                self.printer("-----------------------------------------")
                self.list_invoice_collection(InvoiceCollection(last_invoice_of_the_year.values()), list_field_names=None, header=None, order_field_names=None,
                    table_mode=table_mode, output_filename=output_filename)

        if internal_options.needs_refresh and force_refresh:
            self.db.store_internal_options(self.db.DEFAULT_INTERNAL_OPTIONS)
        return validation_result, scan_events, updated_invoice_collection

    def delete_failing_invoices(self, validation_result, connection=None):
        db = self.db
        with db.connect(connection) as connection:
            year_numbers = {}
            for invoice in validation_result.failing_invoices().values():
                year_numbers.setdefault(invoice.year, []).append(invoice.number)
            for year, numbers in year_numbers.items():
                where = ['year == {}'.format(invoice.year), 'number in ({})'.format(', '.join(str(number) for number in numbers))]
                db.delete('invoices', where=where, connection=connection)
                    
    ## functions
    def filter_invoice_collection(self, invoice_collection, filters, date_from=None, date_to=None):
        if filters is None:
            filters = []
        else:
            filters = list(filters)
        if date_from is not None:
            filters.append(lambda invoice: invoice.date >= date_from)
        if date_to is not None:
            filters.append(lambda invoice: invoice.date <= date_to)
        if filters:
            self.logger.debug("applicazione filtri su {} fatture...".format(len(invoice_collection)))
            for filter_source in filters:
                self.logger.debug("applicazione filtro {!r} su {} fatture...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        return invoice_collection

    def validate_invoice_collection(self, validation_result, invoice_collection, user_validators=()):
        self.logger.debug("validation of {} invoices...".format(len(invoice_collection)))
        invoice_collection.sort()

        # verify fields definition:
        for invoice in invoice_collection:
            invoice.validate(validation_result=validation_result)

        # verify first/last name exchange:
        tnd = {}
        ntd = {}
        for invoice in invoice_collection:
            if invoice.tax_code in tnd:
                nd = tnd[invoice.tax_code]
                for i_name, i_doc_filenames in nd.items():
                    if i_name != invoice.name:
                        message = "fattura {f}: il codice_fiscale {t!r} è associato al nome {n!r}, mentre è stato associato ad un altro nome {pn!r} in #{c} fatture".format(
                            f=invoice.doc_filename,
                            t=invoice.tax_code,
                            n=invoice.name,
                            pn=i_name,
                            c=len(i_doc_filenames),
                        )
                        validation_result.add_warning(invoice, InvoiceMultipleNamesError, message)
            tnd.setdefault(invoice.tax_code, {}).setdefault(invoice.name, []).append(invoice.doc_filename)
            if invoice.name in ntd:
                td = ntd[invoice.name]
                for i_tax_code, i_doc_filenames in td.items():
                    if i_tax_code != invoice.tax_code:
                        message = "fattura {f}: il nome {n!r} è associato al codice_fiscale {t!r}, mentre è stato associato ad un altro codice_fiscale {pt!r} in #{c} fatture".format(
                            f=invoice.doc_filename,
                            t=invoice.tax_code,
                            n=invoice.name,
                            pt=i_tax_code,
                            c=len(i_doc_filenames),
                        )
                        validation_result.add_warning(invoice, InvoiceMultipleTaxCodesError, message)
            ntd.setdefault(invoice.name, {}).setdefault(invoice.tax_code, []).append(invoice.doc_filename)

        # verify multiple invoices in same day
        cd = {}
        for invoice in invoice_collection:
            cd.setdefault((invoice.tax_code, invoice.date), []).append(invoice.doc_filename)
        for (tax_code, date), doc_filenames in cd.items():
            if len(doc_filenames) > 1:
                for doc_filename in doc_filenames:
                    message = "fattura {f}: sono state emesse {c} fatture nello stesso giorno".format(
                        f=doc_filename,
                        c=len(doc_filenames),
                    )
                    validation_result.add_warning(invoice, InvoiceMultipleInvoicesPerDayError, message)
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
                for validator, compiled_validator in user_validators:
                    if compiled_validator.filter_function(invoice):
                        if not compiled_validator.check_function(invoice):
                            validation_result.add_error(invoice, InvoiceUserValidatorError, "fattura {}: {}".format(invoice.doc_filename, validator.message))
                            failed = True
                            
                      
                if not failed:
                    expected_number += 1
                    numbers.setdefault(invoice.number, []).append(invoice)
                    prev_doc, prev_date = invoice.doc_filename, invoice.date
                

        self.logger.debug("validazione di {} fatture completata con {} errori e {} warning".format(
            len(invoice_collection),
            validation_result.num_errors(),
            validation_result.num_warnings()))
        return validation_result

    def get_doc_file(self, output_filename):
        if output_filename is None:
            return self.printer.stream
        else:
            return output_filename

# TODO remove    def write_table(self, table, data, output_filename=None):
# TODO remove        if output_filename is not None:
# TODO remove            table.write(data=data, to=output_filename)
# TODO remove        else:
# TODO remove            if table.mode == conf.TABLE_MODE_XLSX:
# TODO remove                raise InvoiceArgumentError("non è possibile produrre una tabella in formato {} su terminale; utilizzare --output/-o".format(table.mode))
# TODO remove            table.write(data=data, to=self.printer)

    def list_invoice_collection(self, invoice_collection, list_field_names=None, header=None, order_field_names=None, table_mode=None, output_filename=None):
        list_field_names = self.db.get_config_option('list_field_names', list_field_names)
        header = self.db.get_config_option('header', header)
        table_mode = self.db.get_config_option('table_mode', table_mode)
        invoice_collection.sort()
        invoices = list(invoice_collection)
        if order_field_names:
            for reverse, field_name in reversed(order_field_names):
                invoices.sort(key=lambda invoice: getattr(invoice, field_name), reverse=reverse)
        if list_field_names is None:
            list_field_names = Invoice._fields
        if header:
            header = [Invoice.get_field_translation(field_name) for field_name in list_field_names]
        digits = 1 + int(math.log10(max(1, len(invoices))))
        with document(file=self.get_doc_file(output_filename), mode=table_mode, logger=self.logger) as doc:
            page_template = doc.create_page_template(
                field_names=list_field_names,
                header=header,
                convert={
                    'number': lambda n: "{n:0{digits}d}".format(n=n, digits=digits),
                    'income': lambda i: "{:.2f}".format(i),
                },
                align={
                    'number': '>',
                    'income': '>',
                },
            )
            doc.add_page(page_template, invoices)

    def dump_invoice_collection(self, invoice_collection):
        invoice_collection.sort()
        digits = 1 + int(math.log10(max(1, len(invoice_collection))))
        for invoice in invoice_collection:
            self.printer("""\
fattura:                   {doc_filename!r}
  anno/numero:             {year}/{number:0{digits}d}
  città/data:              {city}/{date}
  nome:                    {name}
  codice fiscale:          {tax_code}
  incasso:                 {income:.2f} [{currency}]""".format(digits=digits, **invoice._asdict()))

    def report_invoice_collection(self, invoice_collection):
        invoice_collection.sort()
        for year in invoice_collection.years():
            year_invoices = invoice_collection.filter(lambda invoice: invoice.year == year)
            td = collections.OrderedDict()
            wd = collections.OrderedDict()
            for invoice in year_invoices:
                td.setdefault(invoice.tax_code, []).append(invoice)
                wd.setdefault(self.get_week_number(invoice.date), []).append(invoice)
            self.printer("""\
anno                       {year}
  * incasso totale:        {total_income:.2f}
  * numero di fatture:     {num_invoices}
  * numero di clienti:     {num_clients}\
""".format(
                year=year,
                total_income=sum(invoice.income for invoice in year_invoices),
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
                counter = collections.Counter()
                for invoice in invoices:
                    counter[invoice.date] += 1
                day_names = ['LU', 'MA', 'ME', 'GI', 'VE', 'SA', 'DO']
                days = []
                dates = sorted(counter.keys())
                for date in dates:
                    day = date.weekday()
                    count = counter[date]
                    days.append("{} {}[{}]".format(date, day_names[day], count))
                week_total_income = sum(invoice.income for invoice in invoices)
                if total_income != 0.0:
                    week_income_percentage = week_total_income / total_income
                else:
                    week_income_percentage = 0.0
                first_date, last_date = self.get_week_range(year, week)
                self.printer("""\
    + settimana:           {week} [{first_date} -> {last_date}]:
      numero di fatture:   {num_invoices}
      giorni:              {days}
      incasso totale:      {week_total_income:.2f}
      incasso percentuale: {week_income_percentage:.2%}
""".format(
                    week=week,
                    num_invoices=len(invoices),
                    days=', '.join(days),
                    first_date=first_date,
                    last_date=last_date,
                    total_income=total_income,
                    week_total_income=week_total_income,
                    week_income_percentage=week_income_percentage,
                ))
        

    def impl_help(self, *, parser_dict, argument):
        if not argument in parser_dict:
            if argument == 'snow':
                snow.set_flake_symbols()
                snow.make_it_snow()
            elif argument == 'money':
                snow.set_currency_symbols()
                snow.make_it_snow()
            elif argument == 'errors':
                l = []
                for exc in InvoiceValidationError.subclasses():
                    l.append((exc.exc_code(), exc.exc_description()))
                l.sort(key=lambda x: x[0])
                for exc_code, exc_description in l:
                    self.printer("[{}] {}".format(exc_code, exc_description))
            else:
                self.logger.error("non è disponibile alcun help per il comando sconosciuto {!r}")
        else:
            parser = parser_dict[argument]
            parser.print_help(file=self.printer.stream)

