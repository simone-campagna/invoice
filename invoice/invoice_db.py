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

from .conf import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
from .error import InvoiceError
from .invoice import Invoice
from .invoice_collection import InvoiceCollection
from .database.db import Db, DbError
from .database.table import Table
from .database.db_types import Str, Int, Float, Date, DateTime, Path, Bool
from .validation_result import ValidationResult

class InvoiceDb(Db):
    Pattern = collections.namedtuple('Pattern', ('pattern'))
    Configuration = collections.namedtuple('Configuration', ('warning_mode', 'error_mode', 'partial_update', 'remove_orphaned'))
    Version = collections.namedtuple('Version', ('major', 'minor', 'patch'))
    ScanDateTime = collections.namedtuple('ScanDateTime', ('scan_date_time', 'doc_filename'))
    VERSION = Version(
        major=VERSION_MAJOR,
        minor= VERSION_MINOR,
        patch= VERSION_PATCH)
    DEFAULT_CONFIGURATION = Configuration(
        warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
        error_mode=ValidationResult.ERROR_MODE_DEFAULT,
        remove_orphaned=False,
        partial_update=True)
    
    TABLES = {
        'version': Table(
            fields=(
                ('major', Int()),
                ('minor', Int()),
                ('patch', Int()),
            ),
            dict_type=Version,
        ),
        'configuration': Table(
            fields=(
                ('warning_mode', Str()),
                ('error_mode', Str()),
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

    def check(self):
        super().check()
        with self.connect() as connection:
            version = self.load_version(connection=connection)
            if not self.version_is_valid(version):
                vdb = "{}.{}.{}".format(*version)
                vcl = "{}.{}.{}".format(*self.VERSION)
                raise DbError("versione del database {} non compatibile con quella del client {}".format(vdb, vcl))

    def version_is_valid(self, version):
        return version[:-1] == self.VERSION[:-1]
            
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
            self.write('version', [self.VERSION], connection=connection)

    @classmethod
    def make_pattern(cls, pattern):
        if not isinstance(pattern, cls.Pattern):
            pattern = cls.Pattern(pattern=Path.db_to(pattern))
        return pattern

    @classmethod
    def make_patterns(cls, patterns):
        pattern_list = []
        for pattern in patterns:
            pattern_list.append(cls.make_pattern(pattern))
        return pattern_list

    @classmethod
    def non_patterns(cls, patterns):
        patterns = cls.make_patterns(patterns)
        return list(filter(lambda pattern: not cls.is_pattern(pattern), patterns))

    @classmethod
    def is_pattern(cls, pattern):
        if isinstance(pattern, cls.Pattern):
            pattern = pattern.pattern
        for ch in '*[?':
            if ch in pattern:
                return True
        else:
            return False
 
    def store_patterns(self, patterns, connection=None):
        patterns = self.make_patterns(patterns)
        with self.connect(connection) as connection:
            self.clear('patterns')
            if patterns:
                self.write('patterns', patterns, connection=connection)
        return patterns

    def store_configuration(self, configuration, connection=None):
        with self.connect(connection) as connection:
            default_configuration = self.load_configuration(connection=connection)
            self.clear('configuration')
            data = {}
            for field in self.Configuration._fields:
                value = getattr(configuration, field)
                if value is None:
                    value = getattr(default_configuration, field)
                data[field] = value
            configuration = self.Configuration(**data)
            self.warn_remove_orphaned(configuration.remove_orphaned)
            self.write('configuration', [configuration], connection=connection)
        return configuration

    def load_patterns(self, connection=None):
        with self.connect(connection) as connection:
            patterns = list(self.read('patterns', connection=connection))
            return patterns

    def default_configuration(self, connection=None):
        return self.DEFAULT_CONFIGURATION

    def load_configuration(self, connection=None):
        with self.connect(connection) as connection:
            configurations = list(self.read('configuration', connection=connection))
            if len(configurations) == 0:
                configuration = self.DEFAULT_CONFIGURATION
            else:
                configuration = configurations[-1]
        self.warn_remove_orphaned(configuration.remove_orphaned)
        return configuration

    def store_invoice_collection(self, invoice_collection, connection=None): # pragma: no cover
        with self.connect(connection) as connection:
            self.write('invoices', invoice_collection, connection=connection)
            
    def load_version(self, connection=None):
        with self.connect(connection) as connection:
            versions = list(self.read('version', connection=connection))
            if len(versions) == 0:
                raise DbError("tabella 'version' non trovata")
            else:
                version = versions[-1]
        return version

    def store_version(self, version, connection=None):
        with self.connect(connection) as connection:
            self.clear('version')
            self.write('version', [version])
        
    def load_invoice_collection(self, connection=None):
        invoice_collection = InvoiceCollection()
        with self.connect(connection) as connection:
            for invoice in self.read('invoices', connection=connection):
                invoice_collection.add(invoice)
        return invoice_collection
                
    def warn_remove_orphaned(self, remove_orphaned):
        if remove_orphaned:
            self.logger.warning("l'opzione remove_orphaned è pericolosa, in quanto può compromettere la validazione del database!")

