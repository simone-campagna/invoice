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

import datetime
import os
import sqlite3

from .invoice import Invoice
from .database.db import Db
from .database.table import Table
from .database.db_types import Str, Int, Float, Date, DateTime, Path

class InvoiceDb(Db):
    TABLES = {
        'invoices': Table(
            fields=(
                ('ID', Int('PRIMARY KEY')),
                ('doc_filename', Path()),
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
        'scan_dates': Table(
            fields=(
                ('doc_filename', Str('UNIQUE')),
                ('scan_date', DateTime()),
            ),
            dict_type=Invoice,
        ),
    }

    def initialize(self, connection=None):
        min_datetime = DateTime.db_to(datetime.datetime.min)
        with self.connect(connection) as connection:
            super().initialize(connection=connection)
            cursor = connection.cursor()
            sql = """CREATE TRIGGER insert_on_invoices BEFORE INSERT ON invoices
BEGIN
INSERT OR REPLACE INTO scan_dates (doc_filename, scan_date) VALUES (new.doc_filename, {!r});
END""".format(min_datetime)
            self.execute(cursor, sql)
            sql = """CREATE TRIGGER update_on_invoices BEFORE UPDATE ON invoices
BEGIN
INSERT OR REPLACE INTO scan_dates (doc_filename, scan_date) VALUES (new.doc_filename, {!r});
END""".format(min_datetime)
            self.execute(cursor, sql)
            sql = """CREATE TRIGGER delete_on_invoices BEFORE DELETE ON invoices
BEGIN
DELETE FROM scan_dates WHERE doc_filename == old.doc_filename;
END"""
            self.execute(cursor, sql)

