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
import configparser
import datetime
import sqlite3

from . import conf
from .error import InvoiceError, InvoiceVersionError
from .version import Version, VERSION
from .invoice import Invoice
from .invoice_collection import InvoiceCollection
from .database.db import Db, DbError
from .database.db_table import DbTable
from .database.db_types import Str, Int, Float, Date, DateTime, Path, Bool, StrTuple, \
                               BaseSequence, OptionType
from .database.upgrade.upgrader import Upgrader
from .validation_result import ValidationResult

class WarningModeOption(OptionType):
    OPTIONS = ValidationResult.WARNING_MODES

class ErrorModeOption(OptionType):
    OPTIONS = ValidationResult.ERROR_MODES

class StatsGroupOption(OptionType):
    OPTIONS = conf.STATS_GROUPS

class FieldNameOption(OptionType):
    OPTIONS = conf.LIST_FIELD_NAMES

class TableModeOption(OptionType):
    OPTIONS = conf.TABLE_MODES

class FieldNameOptionTuple(BaseSequence):
    SCALAR_TYPE = FieldNameOption
    SEQUENCE_TYPE = tuple

class InvoiceDb(Db):
    Pattern = collections.namedtuple('Pattern', ('pattern', 'skip'))
    Validator = collections.namedtuple('Validator', ('filter_function', 'check_function', 'message'))
    Configuration = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names',
         'show_scan_report', 'table_mode'))
    ScanDateTime = collections.namedtuple('ScanDateTime', ('scan_date_time', 'doc_filename'))
    DEFAULT_CONFIGURATION = Configuration(
        warning_mode=ValidationResult.WARNING_MODE_DEFAULT,
        error_mode=ValidationResult.ERROR_MODE_DEFAULT,
        remove_orphaned=True,
        partial_update=True,
        header=True,
        total=True,
        stats_group=conf.DEFAULT_STATS_GROUP,
        list_field_names=conf.DEFAULT_LIST_FIELD_NAMES,
        show_scan_report=False,
        table_mode=None)
    
    TABLES = {
        'version': DbTable(
            fields=(
                ('major', Int()),
                ('minor', Int()),
                ('patch', Int()),
            ),
            dict_type=Version,
            singleton=True,
        ),
        'configuration': DbTable(
            fields=(
                ('warning_mode', WarningModeOption()),
                ('error_mode', ErrorModeOption()),
                ('remove_orphaned', Bool()),
                ('partial_update', Bool()),
                ('header', Bool()),
                ('total', Bool()),
                ('stats_group', StatsGroupOption()),
                ('list_field_names', FieldNameOptionTuple()),
                ('show_scan_report', Bool()),
                ('table_mode', TableModeOption()),
            ),
            dict_type=Configuration,
            singleton=True,
        ),
        'patterns': DbTable(
            fields=(
                ('pattern', Path('UNIQUE')),
                ('skip', Bool()),
            ),
            dict_type=Pattern,
            singleton=False,
        ),
        'skip_patterns': DbTable(
            fields=(
                ('pattern', Path('UNIQUE')),
            ),
            dict_type=Pattern,
            singleton=False,
        ),
        'invoices': DbTable(
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
            singleton=False,
        ),
        'validators': DbTable(
            fields=(
                ('filter_function', Str()),
                ('check_function', Str()),
                ('message', Str()),
            ),
            dict_type=Validator,
            singleton=False,
        ),
        'scan_date_times': DbTable(
            fields=(
                ('doc_filename', Str('UNIQUE')),
                ('scan_date_time', DateTime()),
            ),
            dict_type=ScanDateTime,
            singleton=False,
        ),
    }
    def __init__(self, *p_args, **n_args):
        super().__init__(*p_args, **n_args)
        self._configuration = None

    def check(self):
        super().check()
        with self.connect() as connection:
            table_names = self.get_table_names(connection)
            if not 'version' in table_names:
                raise DbError("database {!r}: la versione non è disponibile; è necessario eseguire nuovamente l'inizializzazione".format(self.db_filename))
            version = self.load_version(connection=connection)
            if not self.version_is_valid(version):
                vdb = "{}.{}.{}".format(*version)
                vcl = "{}.{}.{}".format(*VERSION)
                raise InvoiceVersionError("database {!r}: la versione {} non compatibile con quella del client {}".format(self.db_filename, vdb, vcl))

    def version_is_valid(self, version):
        return version[:-1] == VERSION[:-1]
            
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
            self.write('version', [VERSION], connection=connection)

    @classmethod
    def make_validator(cls, filter_function, check_function, message):
        return cls.Validator(filter_function=filter_function, check_function=check_function, message=message)

    @classmethod
    def make_pattern(cls, pattern):
        if not isinstance(pattern, cls.Pattern):
            if pattern.startswith('!'):
                skip = True
                pattern = pattern[1:]
            else:
                skip = False
            pattern = cls.Pattern(pattern=Path.db_to(pattern), skip=skip)
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
                
    def get_config_option(self, option, value, connection=None):
        if value is None:
            if self._configuration is None:
                self._configuration = self.load_configuration(connection=connection)
            value = getattr(self._configuration, option)
        return value

    def load_validators(self, connection=None):
        validators = []
        with self.connect(connection) as connection:
            table_names = self.get_table_names(connection=connection)
            if 'validators' in table_names:
                for validator in self.read('validators', connection=connection):
                    validators.append(validator)
        return validators

    def upgrade(self):
        Upgrader.full_upgrade(db=self)

    def export_table(self, table_name, filename, connection=None):
        records = self.read(table_name, connection=connection)
        config = configparser.ConfigParser()
        table_info = self.TABLES[table_name]
        fields = table_info.fields
        for c, record in enumerate(records):
            section_name = "{}_{}".format(table_name, c)
            config.add_section(section_name)
            section = config[section_name]
            for field_name in table_info.field_names:
                section[field_name] = str(fields[field_name].db_to(getattr(record, field_name)))
        with open(filename, "w") as f_out:
            config.write(f_out)

    def import_table(self, table_name, filename, connection=None):
        config = configparser.ConfigParser()
        config.read(filename)
        table_info = self.TABLES[table_name]
        fields = table_info.fields
        dict_type = table_info.dict_type
        records = []
        for section_name in config.sections():
            section = config[section_name]
            d = {}
            for field_name in table_info.field_names:
                d[field_name] = fields[field_name].db_from(section[field_name])
            record = dict_type(**d)
            records.append(record)
        self.write(table_name, records, connection=connection)
