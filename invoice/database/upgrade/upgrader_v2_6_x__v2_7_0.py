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
    'Upgrader_v2_6_x__v2_7_0',
]

import collections
import sqlite3

from ..db_types import Bool, Str, StrTuple, Int, Float
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version
from ...validation_result import ValidationResult
from ... import conf

class Upgrader_v2_6_x__v2_7_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 6, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 7, 0)
    CONFIGURATION_TABLE_v2_6_x = DbTable(
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
    )
    CONFIGURATION_TABLE_v2_7_0 = DbTable(
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
            ('spy_notify_level', Str()),
            ('spy_delay', Float()),
        ),
    )
    INTERNAL_OPTIONS_TABLE_v2_7_0 = DbTable(
        fields=(
            ('needs_refresh', Bool()),
        ),
    )

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        def new_to_old(new_data):
            return {
                'spy_notify_level': conf.DEFAULT_SPY_NOTIFY_LEVEL,
                'spy_delay': conf.DEFAULT_SPY_DELAY,
            }
        return self.do_downgrade(
            table_name="configuration",
            old_table=self.CONFIGURATION_TABLE_v2_6_x,
            new_table=self.CONFIGURATION_TABLE_v2_7_0,
            new_to_old=new_to_old,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
        with db.connect() as connection:
            cursor = connection.cursor()
            db.execute(cursor, "DROP TABLE internal_options;")
            db.execute(cursor, "DROP TRIGGER insert_on_validators;")
            db.execute(cursor, "DROP TRIGGER update_on_validators;")
            db.execute(cursor, "DROP TRIGGER delete_on_validators;")

    def impl_upgrade(self, db, version_from, version_to, connection=None):
        def old_to_new(old_data):
            return {
                'spy_notify_level': conf.DEFAULT_SPY_NOTIFY_LEVEL,
                'spy_delay': conf.DEFAULT_SPY_DELAY,
            }
        self.do_upgrade(
            table_name="configuration",
            old_table=self.CONFIGURATION_TABLE_v2_6_x,
            new_table=self.CONFIGURATION_TABLE_v2_7_0,
            old_to_new=old_to_new,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
        with db.connect() as connection:
            cursor = connection.cursor()
            # internal options
            try:
                db.create_table('internal_options', self.INTERNAL_OPTIONS_TABLE_v2_7_0.fields, connection=connection)
            except sqlite3.OperationalError:
                pass
            # validators triggers
            sql = """CREATE TRIGGER insert_on_validators BEFORE INSERT ON validators
BEGIN
UPDATE internal_options SET needs_refresh = 1 WHERE NOT needs_refresh;
END"""
            db.execute(cursor, sql)
            sql = """CREATE TRIGGER update_on_validators BEFORE UPDATE ON validators
BEGIN
UPDATE internal_options SET needs_refresh = 1 WHERE NOT needs_refresh;
END"""
            db.execute(cursor, sql)
            sql = """CREATE TRIGGER delete_on_validators BEFORE DELETE ON validators
BEGIN
UPDATE internal_options SET needs_refresh = 1 WHERE NOT needs_refresh;
END"""
            db.execute(cursor, sql)

