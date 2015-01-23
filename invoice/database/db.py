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

from .log import get_default_logger

class Db(object):
    TABLES = {}
    def __init__(self, db_filename, logger=None):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        self.db_filename = db_filename

    def connect(self):
        return sqlite3.connect(self._filename)

    def get_table_names(self):
        with self.connect() as connection:
            cursor = connection.cursor()
            return tuple(cursor.execute("SELECT name FROM sqlite_maste WHERE type == 'table';"))

    def create_table(self, table_name, table_fields):
        with self.connect() as connection:
            cursor = connection.cursor()
    
            self.logger.info("creating {} table...".format(table_name))
            sql = """CREATE TABLE {table_name} ({table_fields});""".format(
                table_name=table_name,
                table_fields=', '.join("{} {} {}".format(field, field_type.db_typename(), " ".join(field_type.db_create_args())) for field, field_type in table_fields.iteritems())
            )
            cursor.execute(sql)

    def initialize(self):
        if os.path.exists(self.db_filename):
            table_names = self.get_table_names()
        else:
            table_names = ()
        for table_name, table_fields in self.TABLES.items():
            if not table in table_names:
                self.create_table(table_name, table_fields)

