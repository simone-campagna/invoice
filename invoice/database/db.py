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
    'Db',
]

import os
import sqlite3

class Db(object):
    TABLES = {}
    def __init__(self, db_filename, logger):
        self.logger = logger
        self.db_filename = db_filename

    def connect(self, connection=None):
        if connection:
            return connection
        else:
            return sqlite3.connect(self.db_filename)

    def execute(self, cursor, sql, values=None):
        if values is None:
            self.logger.debug("executing query {!r}...".format(sql))
            return cursor.execute(sql)
        else:
            self.logger.debug("executing query {!r} with values {!r}...".format(sql, values))
            return cursor.execute(sql, values)

    def get_table_names(self, connection=None):
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            return tuple(self.execute(cursor, "SELECT name FROM sqlite_master WHERE type == 'table';"))

    def create_table(self, table_name, table_fields, connection=None):
        with self.connect(connection) as connection:
            cursor = connection.cursor()
    
            self.logger.info("creating {} table...".format(table_name))
            sql = """CREATE TABLE {table_name} ({table_fields});""".format(
                table_name=table_name,
                table_fields=', '.join("{} {} {}".format(field, field_type.db_typename(), " ".join(field_type.db_create_args())) for field, field_type in table_fields.items())
            )
            self.execute(cursor, sql)

    def initialize(self, connection):
        if os.path.exists(self.db_filename):
            table_names = self.get_table_names(connection=connection)
        else:
            table_names = ()
        for table_name, table in self.TABLES.items():
            if not table in table_names:
                self.create_table(table_name, table.fields, connection=connection)

    def read(self, table_name, where=None, connection=None):
        if where:
            if isinstance(where, str):
                 where_list = [where]
            else:
                 where_list = where
            where = " WHERE ({})".format(" AND ".join("( {} )".format(w) for w in where_list))
        else:
            where = ""
        table = self.TABLES[table_name]
        field_names = table.field_names
        fields = table.fields
        sql = """SELECT {field_names} FROM {table_name}{where};""".format(
            field_names=', '.join(field_names),
            table_name=table_name,
            where=where,
        )
        records = []
        dict_type = table.dict_type
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            for values in self.execute(cursor, sql):
                record_d = dict((field_name, fields[field_name].db_from(value)) for field_name, value in zip(field_names, values))
                records.append(dict_type(**record_d))
        return records
        
    def write(self, table_name, records, connection=None):
        table = self.TABLES[table_name]
        field_names = table.field_names
        fields = table.fields
        sql = """INSERT INTO {table_name} ({field_names}) VALUES ({placeholders});""".format(
            table_name=table_name,
            field_names=', '.join(field_names),
            placeholders=', '.join('?' for i in field_names),
        )
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            for values in records:
                record = [fields[field_name].db_to(value) for field_name, value in zip(field_names, values)]
                self.execute(cursor, sql, record)
