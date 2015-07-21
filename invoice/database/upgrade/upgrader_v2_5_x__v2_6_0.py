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
    'Upgrader_v2_5_x__v2_6_0',
]

import collections

from ..db_types import Bool, Str, StrTuple, Int
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version
from ... import conf

class Upgrader_v2_5_x__v2_6_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 5, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 6, 0)
    Configuration_v2_5_x = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names',
         'show_scan_report', 'table_mode', 'max_interruption_days'))
    CONFIGURATION_TABLE_v2_5_x = DbTable(
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
            ('table_mode', Str()),
            ('max_interruption_days', Int()),
        ),
        dict_type=Configuration_v2_5_x,
    )
    Configuration_v2_6_0 = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'warning_suppression', 'error_mode', 'error_suppression',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names',
         'show_scan_report', 'table_mode',
         'max_interruption_days'))
    CONFIGURATION_TABLE_v2_6_0 = DbTable(
        fields=(
            ('warning_mode', Str()),
            ('warning_suppression', StrTuple()),
            ('error_mode', Str()),
            ('error_suppression', StrTuple()),
            ('remove_orphaned', Bool()),
            ('partial_update', Bool()),
            ('header', Bool()),
            ('total', Bool()),
            ('stats_group', Str()),
            ('list_field_names', StrTuple()),
            ('show_scan_report', Bool()),
            ('table_mode', Str()),
            ('max_interruption_days', Int()),
        ),
        dict_type=Configuration_v2_6_0,
    )
    def impl_downgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            new_field_names = self.Configuration_v2_6_0._fields
            sql = """SELECT {field_names} FROM configuration;""".format(field_names=", ".join(new_field_names))
            r = list(db.execute(cursor, sql))[-1]
            new_values = dict(zip(new_field_names, r))
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_5_x.fields, connection=connection)
            old_field_names = self.Configuration_v2_5_x._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(old_field_names),
                placeholders=', '.join('?' for field in old_field_names),
            )
            db.execute(cursor, sql, tuple(new_values[field_name] for field_name in old_field_names))
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT * FROM configuration;"""
            values = list(db.execute(cursor, sql))[-1]
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_6_0.fields, connection=connection)
            values +=  (StrTuple.db_to(()), StrTuple.db_to(()))
            field_names = self.Configuration_v2_6_0._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(field_names),
                placeholders=', '.join('?' for field in field_names),
            )
            db.execute(cursor, sql, values)
