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
    'InvoiceDb',
]

import collections
import datetime
import glob
import os
import sqlite3
import time

from .error import InvoiceError
from .invoice import Invoice
from .invoice_reader import InvoiceReader
from .invoice_collection import InvoiceCollection
from .database.db import Db
from .database.table import Table
from .database.db_types import Str, Int, Float, Date, DateTime, Path, Bool

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

class InvoiceDb(Db):
    Pattern = collections.namedtuple('Pattern', ('pattern'))
    Configuration = collections.namedtuple('Configuration', ('remove_orphaned', 'partial_update'))
    ScanDateTime = collections.namedtuple('ScanDateTime', ('scan_date_time', 'doc_filename'))
    DEFAULT_CONFIGURATION = Configuration(remove_orphaned=False, partial_update=True)
    TABLES = {
        'configuration': Table(
            fields=(
                ('remove_orphaned', Bool()),
                ('partial_update', Bool()),
            ),
            dict_type=Configuration,
        ),
        'patterns': Table(
            fields=(
                ('pattern', Path('UNIQUE')),
            ),
            dict_type=Pattern,
        ),
        'invoices': Table(
            fields=(
                ('ID', Int('PRIMARY KEY')),
                ('doc_filename', Path('UNIQUE')),
                ('year', Int()),
                ('number', Int()),
                ('name', Str()),
                ('tax_code', Str()),
                ('city', Str()),
                ('date', Date()),
                ('income', Float()),
                ('currency', Str()),
            ),
            dict_type=Invoice,
        ),
        'scan_date_times': Table(
            fields=(
                ('doc_filename', Str('UNIQUE')),
                ('scan_date_time', DateTime()),
            ),
            dict_type=ScanDateTime,
        ),
    }

    def impl_initialize(self, connection=None):
        min_datetime = DateTime.db_to(datetime.datetime(1900, 1, 1))
        with self.connect(connection) as connection:
            super().impl_initialize(connection=connection)
            cursor = connection.cursor()
            sql = """CREATE TRIGGER insert_on_invoices BEFORE INSERT ON invoices
BEGIN
INSERT OR REPLACE INTO scan_date_times (doc_filename, scan_date_time) VALUES (new.doc_filename, {!r});
END""".format(min_datetime)
            self.execute(cursor, sql)
            sql = """CREATE TRIGGER update_on_invoices BEFORE UPDATE ON invoices
BEGIN
INSERT OR REPLACE INTO scan_date_times (doc_filename, scan_date_time) VALUES (new.doc_filename, {!r});
END""".format(min_datetime)
            self.execute(cursor, sql)
            sql = """CREATE TRIGGER delete_on_invoices BEFORE DELETE ON invoices
BEGIN
DELETE FROM scan_date_times WHERE doc_filename == old.doc_filename;
END"""
            self.execute(cursor, sql)

    def show_configuration(self, print_function=print, connection=None):
        with self.connect(connection) as connection:
            print_function("patterns:")
            for pattern in self.load_patterns(connection=connection):
                print_function("  + {!r}".format(pattern))
            print_function()
            print_function("configuration:")
            configuration = self.load_configuration(connection=connection)
            for field_name in self.Configuration._fields:
                print_function("  + {:20s} = {!r}".format(field_name, getattr(configuration, field_name)))

    def configure(self, patterns, partial_update=None, remove_orphaned=None, connection=None):
        with self.connect(connection) as connection:
            default_configuration = self.load_configuration(connection=connection)
            self.delete('configuration')
            if remove_orphaned is None:
                remove_orphaned = default_configuration.remove_orphaned
            if partial_update is None:
                partial_update = default_configuration.partial_update
            configuration = self.Configuration(
                remove_orphaned=remove_orphaned,
                partial_update=partial_update,
            )
            self.warn_remove_orphaned(remove_orphaned)
            self.write('configuration', [configuration])
            if patterns:
                self.write('patterns', ((pattern, ) for pattern in patterns))

    def load_patterns(self, connection=None):
        with self.connect(connection) as connection:
            patterns = list(self.read('patterns', connection=connection))
            return patterns

    def load_configuration(self, connection=None):
        with self.connect(connection) as connection:
            configurations = list(self.read('configuration', connection=connection))
            if len(configurations) == 0:
                configuration = self.DEFAULT_CONFIGURATION
            else:
                configuration = configurations[-1]
        return configuration

    def store_invoice_collection(self, invoice_collection, connection=None):
        with self.connect(connection) as connection:
            self.write('invoices', invoice_collection, connection=connection)
            

    def load_invoice_collection(self, connection=None):
        invoice_collection = InvoiceCollection()
        with self.connect(connection) as connection:
            for invoice in self.read('invoices', connection=connection):
                invoice_collection.add(invoice)
        return invoice_collection
                
    def warn_remove_orphaned(self, remove_orphaned):
        if remove_orphaned:
            self.logger.warning("remove_orphaned option can threaten db validation!")
    def scan(self, warnings_mode=InvoiceCollection.WARNINGS_MODE_DEFAULT, raise_on_error=False, partial_update=None, remove_orphaned=None, connection=None):
        found_doc_filenames = set()
        file_date_times = FileDateTimes()
        updated_invoice_collection = InvoiceCollection()
        removed_doc_filenames = []
        with self.connect(connection) as connection:
            configuration = self.load_configuration(connection)
            if remove_orphaned is None:
                remove_orphaned = configuration.remove_orphaned
            self.warn_remove_orphaned(remove_orphaned)
            if partial_update is None:
                partial_update = configuration.partial_update

            for pattern in self.load_patterns(connection=connection):
                for doc_filename in glob.glob(pattern.pattern):
                    found_doc_filenames.add(Path.db_to(doc_filename))
            doc_filename_d = {}
            for scan_date_time in self.read('scan_date_times', connection=connection):
                doc_filename_d[scan_date_time.doc_filename] = scan_date_time.scan_date_time

            result = []
            scanned_doc_filenames = set()

            # update scanned invoices
            invoice_collection = self.load_invoice_collection()
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
                        self.logger.error("cannot read invoice from {!r}: {}: {}".format(doc_filename, type(err).__name__, err))
                        continue
                    updated_invoice_collection.add(invoice_reader(doc_filename))
                    if existing:
                        old_invoices.append(invoice)
                    else:
                        new_invoices.append(invoice)
                    scan_date_times.append(self.ScanDateTime(doc_filename=invoice.doc_filename, scan_date_time=file_date_times[invoice.doc_filename]))
                validation_result = updated_invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
                if validation_result.num_errors():
                    message = "validation failed - {} errors found".format(validation_result.num_errors())
                    if not partial_update:
                        raise InvoiceError(message)
                    else:
                        old_invoices = validation_result.filter_validated_invoices(old_invoices)
                        new_invoices = validation_result.filter_validated_invoices(new_invoices)
                        if old_invoices or new_invoices or removed_doc_filenames:
                            self.logger.warning(message + ' - partial update')
                if old_invoices:
                    self.update('invoices', 'doc_filename', old_invoices, connection=connection)
                if new_invoices:
                    self.write('invoices', new_invoices, connection=connection)
                self.update('scan_date_times', 'doc_filename', scan_date_times, connection=connection)
            if removed_doc_filenames:
                for doc_filename in removed_doc_filenames:
                    self.delete('invoices', '''doc_filename == {!r}'''.format(doc_filename), connection=connection)
        return updated_invoice_collection
