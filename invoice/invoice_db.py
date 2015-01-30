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
import sqlite3

from .error import InvoiceError
from .invoice import Invoice
from .invoice_collection import InvoiceCollection
from .database.db import Db
from .database.table import Table
from .database.db_types import Str, Int, Float, Date, DateTime, Path, Bool

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

    def show_configuration(self, printer=print, connection=None):
        with self.connect(connection) as connection:
            printer("patterns:")
            for pattern in self.load_patterns(connection=connection):
                printer("  + {!r}".format(pattern))
            printer()
            printer("configuration:")
            configuration = self.load_configuration(connection=connection)
            for field_name in self.Configuration._fields:
                printer("  + {:20s} = {!r}".format(field_name, getattr(configuration, field_name)))

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
        self.warn_remove_orphaned(configuration.remove_orphaned)
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
            self.logger.warning("l'opzione remove_orphaned è pericolosa, in quanto può compromettere la validazione del database!")

