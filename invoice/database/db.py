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
    'DbError',
    'Db',
]

import os
import sqlite3

class DbError(Exception):
    pass

class Db(object):
    TABLES = {}
    def __init__(self, db_filename, logger):
        self.logger = logger
        self.db_filename = db_filename
        self.logger.info("il db file è {}".format(self.db_filename))

    def check_existence(self):
        if not os.path.exists(self.db_filename):
            raise DbError("database {!r} non inizializzato".format(self.db_filename))

    def check(self):
        self.check_existence()

    def connect(self, connection=None):
        if connection:
            return connection
        else:
            return sqlite3.connect(self.db_filename)

    def execute(self, cursor, sql, values=None):
        if values is None:
            self.logger.debug("esecuzione della query {!r}...".format(sql))
            return cursor.execute(sql)
        else:
            self.logger.debug("esecuzione della query {!r} con valori {!r}...".format(sql, values))
            return cursor.execute(sql, values)

    def get_table_names(self, connection=None):
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            return tuple(row[0] for row in self.execute(cursor, "SELECT name FROM sqlite_master WHERE type == 'table';"))

    def create_table(self, table_name, table_fields, connection=None):
        with self.connect(connection) as connection:
            cursor = connection.cursor()
    
            self.logger.info("creazione della tabella {!r}...".format(table_name))
            sql = """CREATE TABLE {table_name} ({table_fields});""".format(
                table_name=table_name,
                table_fields=', '.join("{} {} {}".format(field, field_type.db_typename(), " ".join(field_type.db_create_args())) for field, field_type in table_fields.items())
            )
            self.execute(cursor, sql)

    def initialize(self):
        if not os.path.exists(self.db_filename):
            dirname, basename = os.path.split(self.db_filename)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)
        self.impl_initialize()

    def impl_initialize(self, connection=None):
        with self.connect(connection) as connection:
            table_names = self.get_table_names(connection=connection)
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
        if table.singleton:
            limit = " ORDER BY rowid DESC LIMIT 1";
        else:
            limit = ""
        sql = """SELECT {field_names} FROM {table_name}{where}{limit};""".format(
            field_names=', '.join(field_names),
            table_name=table_name,
            where=where,
            limit=limit,
        )
        records = []
        dict_type = table.dict_type
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            for values in self.execute(cursor, sql):
                record_d = dict((field_name, fields[field_name].db_from(value)) for field_name, value in zip(field_names, values))
                records.append(dict_type(**record_d))
        return records
        
    def update(self, table_name, key, records, connection=None):
        table = self.TABLES[table_name]
        field_names = [field_name for field_name in table.field_names if field_name != key]
        sql = """UPDATE {table_name} SET {field_values} WHERE {key} == ?;""".format(
            table_name=table_name,
            field_values=', '.join("{} = ?".format(field_name) for field_name in field_names),
            key=key,
        )
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            for record in records:
                values = [getattr(record, field_name) for field_name in field_names] + [getattr(record, key)]
                self.execute(cursor, sql, values)

    def drop(self, table_name, connection=None):
        sql = """DROP TABLE {table_name};""".format(
            table_name=table_name,
        )
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            self.execute(cursor, sql)

    def clear(self, table_name, connection=None):
        self.delete(table_name=table_name, where=None, connection=None)

    def delete(self, table_name, where=None, connection=None):
        if where:
            if isinstance(where, str):
                 where_list = [where]
            else:
                 where_list = where
            where = " WHERE ({})".format(" AND ".join("( {} )".format(w) for w in where_list))
        else:
            where = ""
        sql = """DELETE FROM {table_name}{where};""".format(
            table_name=table_name,
            where=where,
        )
        with self.connect(connection) as connection:
            cursor = connection.cursor()
            self.execute(cursor, sql)
    
    def write(self, table_name, records, connection=None):
        table = self.TABLES[table_name]
        field_names = table.field_names
        fields = table.fields
        if table.singleton:
            records = records[-1:]
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
