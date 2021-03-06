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
    'Upgrader_v2_1_x__v2_2_0',
]

import collections

from ..db_types import Bool, Str, StrTuple
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version

class Upgrader_v2_1_x__v2_2_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 1, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 2, 0)
    Configuration_v2_1_x = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names'))
    CONFIGURATION_TABLE_v2_1_x = DbTable(
        fields=(
            ('warning_mode', Str()),
            ('error_mode', Str()),
            ('remove_orphaned', Bool()),
            ('partial_update', Bool()),
            ('header', Bool()),
            ('total', Bool()),
            ('stats_group', Str()),
            ('list_field_names', StrTuple()),
        ),
        dict_type=Configuration_v2_1_x,
    )
    Configuration_v2_2_0 = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names',
         'show_scan_report'))
    CONFIGURATION_TABLE_v2_2_0 = DbTable(
        fields=(
            ('warning_mode', Str()),
            ('error_mode', Str()),
            ('remove_orphaned', Bool()),
            ('partial_update', Bool()),
            ('header', Bool()),
            ('total', Bool()),
            ('stats_group', Str()),
            ('list_field_names', StrTuple()),
            ('show_scan_report', Bool()),
        ),
        dict_type=Configuration_v2_1_x,
    )
    def impl_downgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT * FROM configuration;"""
            v_list = list(db.execute(cursor, sql))
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_1_x.fields, connection=connection)
            field_names = self.Configuration_v2_1_x._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(field_names),
                placeholders=', '.join('?' for field in field_names),
            )
            for v in v_list:
                db.execute(cursor, sql, v[:-1])
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT * FROM configuration;"""
            values = list(db.execute(cursor, sql))[-1]
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_2_0.fields, connection=connection)
            values +=  (False, )
            field_names = self.Configuration_v2_2_0._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(field_names),
                placeholders=', '.join('?' for field in field_names),
            )
            db.execute(cursor, sql, values)
