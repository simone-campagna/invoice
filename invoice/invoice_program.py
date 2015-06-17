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
                   InvoiceWrongNumberError, \
                   InvoiceDuplicatedNumberError, \
                   InvoiceMalformedTaxCodeError, \
                   InvoiceValidationError, \
                   InvoicePartialUpdateError, \
                   InvoiceUserValidatorError, \
                   InvoiceArgumentError

from .invoice_collection import InvoiceCollection
from .invoice_collection_reader import InvoiceCollectionReader
from .invoice_reader import InvoiceReader
from .invoice_db import InvoiceDb
from .invoice import Invoice
from .validation_result import ValidationResult
from .week import WeekManager
from .database.db_types import Path
from .table import Table
from . import conf
from .version import VERSION
from .ee import snow


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
        self.impl_help(parser_dict=parser_dict, command=command)
        return 0

    def program_missing_subcommand(self, *, parser):
        parser.print_help(file=self.printer.stream)
        self.logger.error("deve essere specificato un comando")
        return 1

    def program_version(self, upgrade=False):
        self.impl_version(upgrade=upgrade)
        return 0

    def program_init(self, *, patterns,
                              warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                              error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                              partial_update=True,
                              remove_orphaned=False,
                              header=True,
                              total=True,
                              stats_group=None,
                              list_field_names=None,
                              show_scan_report=None,
                              table_mode=None,
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
            reset=reset,
        )
        return 0

    def program_config(self, *, warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                                error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                                partial_update=True,
                                remove_orphaned=True,
                                header=True,
                                total=True,
                                list_field_names=None,
                                stats_group=None,
                                show_scan_report=None,
                                table_mode=None,
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

    def program_scan(self, *, warning_mode, error_mode, partial_update=True, remove_orphaned=True, show_scan_report=True, table_mode=None, output_filename=None):
        validation_result, invoice_collection = self.impl_scan(
            warning_mode=warning_mode,
            error_mode=error_mode,
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

    def program_stats(self, *, filters=None, date_from=None, date_to=None, stats_group=None, total=None, stats_mode=None, table_mode=None, output_filename=None):
        self.impl_stats(filters=filters, date_from=date_from, date_to=date_to, stats_group=stats_group, total=total, stats_mode=stats_mode, table_mode=table_mode,
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
            self.printer("  + {:20s} = {!r}".format(field_name, getattr(configuration, field_name)))

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
                           warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                           error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                           partial_update=True,
                           remove_orphaned=True,
                           header=True,
                           total=True,
                           stats_group=None,
                           list_field_names=None,
                           show_scan_report=None,
                           table_mode=None,
                           reset=False):
        if list_field_names is None:
            lsit_field_names = conf.DEFAULT_LIST_FIELD_NAMES
        if reset and os.path.exists(self.db_filename):
            self.logger.info("cancellazione del db {!r}...".format(self.db_filename))
            os.remove(self.db_filename)
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
        )
        configuration = self.db.store_configuration(configuration)
        #self.show_configuration(configuration)
        self.check_patterns(patterns)
        patterns = self.db.store_patterns(patterns)
        #self.show_patterns(patterns)

       
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

    def impl_config(self, *, warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
                             error_mode=ValidationResult.ERROR_MODE_DEFAULT,
                             partial_update=True,
                             remove_orphaned=True,
                             header=True,
                             total=True,
                             list_field_names=None,
                             stats_group=None,
                             show_scan_report=None,
                             table_mode=None,
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
   
    def impl_stats(self, *, filters=None, date_from=None, date_to=None, stats_group=None, total=None, stats_mode=None, table_mode=None, output_filename=None):
        total = self.db.get_config_option('total', total)
        table_mode = self.db.get_config_option('table_mode', table_mode)
        self.db.check()
        if filters is None: # pragma: no cover
            filters = ()

        if stats_group is None:
            stats_group = conf.DEFAULT_STATS_GROUP

        if stats_mode is None:
            stats_mode = conf.DEFAULT_STATS_MODE

        invoice_collection = self.filter_invoice_collection(self.db.load_invoice_collection(), filters=filters, date_from=date_from, date_to=date_to)
        invoice_collection.sort()
        if invoice_collection:
            group_translation = {
                conf.STATS_GROUP_YEAR:		'anno',
                conf.STATS_GROUP_MONTH:		'mese',
                conf.STATS_GROUP_WEEK:		'settimana',
                conf.STATS_GROUP_DAY:		'giorno',
                conf.STATS_GROUP_WEEKDAY:	'giorno',
                conf.STATS_GROUP_CLIENT:	Invoice.get_field_translation('tax_code'),
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
                cc_field_name: cc_header,
                'invoice_count':		'fatture',
                'income':			'incasso',
                'income_percentage':		'%incasso',
                'income_bar':			'h(incasso)',
                'invoice_count_bar':		'h(fatture)',
            }
            field_names = (cc_field_name, 'invoice_count', 'invoice_count_bar', 'income', 'income_percentage', 'income_bar')
            if stats_mode == conf.STATS_MODE_SHORT:
                group_field_names = (stats_group, )
                field_names = (cc_field_name, 'invoice_count', 'income', 'income_percentage')
            elif stats_mode == conf.STATS_MODE_LONG:
                group_field_names = (stats_group, 'from', 'to')
                field_names = (cc_field_name, 'invoice_count', 'income', 'income_percentage')
            elif stats_mode == conf.STATS_MODE_FULL:
                group_field_names = (stats_group, 'from', 'to')
                field_names = (cc_field_name, 'invoice_count', 'invoice_count_bar', 'income', 'income_percentage', 'income_bar')
            cum_field_names = ('invoice_count', 'income', 'income_percentage')
            header = tuple(header_d.get(field_name, field_name) for field_name in field_names)
            group_total = ('TOTAL', '', '')
            group_header = tuple(group_translation[field_name] for field_name in group_field_names)
            all_field_names = group_field_names + field_names
            all_header = group_header + header
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
                total_row[stats_group] = "TOTALE"
                total_row[cc_field_name] = cc_total
                total_row['from'] = ""
                total_row['to'] = ""
                total_row['income_bar'] = "--"
                total_row['invoice_count_bar'] = "--"
            total_client_count = len(set(invoice.tax_code for invoice in invoice_collection))
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
                if total:
                    for field_name in cum_field_names:
                        total_row[field_name] += data[field_name]
                    total_row['client_count'] = total_client_count
                if stats_group == conf.STATS_GROUP_CLIENT:
                    data[cc_field_name] = group[0].name
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
            table = Table(
                field_names=all_field_names,
                mode=table_mode,
                header=all_header,
                align=align,
                convert=convert,
                getter=Table.ITEM_GETTER,
                logger=self.logger,
            )
            self.write_table(table=table, data=rows, output_filename=output_filename)


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
    
    def impl_scan(self, warning_mode=None, error_mode=None, partial_update=None, remove_orphaned=None, show_scan_report=None, table_mode=None, output_filename=None):
        self.db.check()
        show_scan_report = self.db.get_config_option('show_scan_report', show_scan_report)
        found_doc_filenames = set()
        db = self.db
        file_date_times = FileDateTimes()
        updated_invoice_collection = InvoiceCollection()
        removed_invoices = []
        validation_result = self.create_validation_result(warning_mode=warning_mode, error_mode=error_mode)
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
                    else:
                        new_invoices.append(invoice)
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
                        #partially_updated_invoices = validation_result.filter_validated_invoices(updated_invoice_collection)
                        #partially_updated_invoice_collection = InvoiceCollection(partially_updated_invoices)
                        #partial_validation_result = self.create_validation_result()
                        #self.validate_invoice_collection(partial_validation_result, partially_updated_invoice_collection)
                        #if partial_validation_result.num_errors():
                        #    raise InvoicePartialUpdateError("validation of partial invoice collection failed")
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
                        self.logger.error("la prima {} fattura contenente errori è:".format(max_errors))
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
                self.printer("ultima fattura inserita per ciascun anno:")
                self.printer("-----------------------------------------")
                self.list_invoice_collection(InvoiceCollection(last_invoice_of_the_year.values()), list_field_names=None, header=None, order_field_names=None,
                    table_mode=table_mode, output_filename=output_filename)

        return validation_result, updated_invoice_collection

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

    def write_table(self, table, data, output_filename=None):
        if output_filename is not None:
            table.write(data=data, to=output_filename)
        else:
            if table.mode == conf.TABLE_MODE_XLSX:
                raise InvoiceArgumentError("non è possibile produrre una tabella in formato {} su terminale; utilizzare --output/-o".format(table.mode))
            table.write(data=data, to=self.printer)

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
        table = Table(
            field_names=list_field_names,
            mode=table_mode,
            header=header,
            convert={
                'number': lambda n: "{n:0{digits}d}".format(n=n, digits=digits),
                'income': lambda i: "{:.2f}".format(i),
            },
            align={
                'number': '>',
                'income': '>',
            },
            logger=self.logger,
        )
        self.write_table(table=table, data=invoices, output_filename=output_filename)

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
        

    def impl_help(self, *, parser_dict, command):
        if not command in parser_dict:
            if command == 'snow':
                snow.set_flake_symbols()
                snow.make_it_snow()
            elif command == 'money':
                snow.set_currency_symbols()
                snow.make_it_snow()
            else:
                self.logger.error("non è disponibile alcun help per il comando sconosciuto {!r}")
        else:
            parser = parser_dict[command]
            parser.print_help(file=self.printer.stream)

