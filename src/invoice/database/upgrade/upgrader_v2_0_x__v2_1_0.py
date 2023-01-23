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
    'Upgrader_v2_0_x__v2_1_0',
]

import collections

from ..db_types import Path, Bool
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version

class Upgrader_v2_0_x__v2_1_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 0, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 1, 0)
    Pattern_v2_0_x = collections.namedtuple('Pattern_v2_0_x', ('pattern', 'skip'))
    PATTERNS_TABLE_v2_0_x = DbTable(
        fields=(
            ('pattern', Path('UNIQUE')),
        ),
        dict_type=Pattern_v2_0_x,
    )
    Pattern_v2_1_0 = collections.namedtuple('Pattern_v2_1_x', ('pattern', ))
    PATTERNS_TABLE_v2_1_0 = DbTable(
        fields=(
            ('pattern', Path('UNIQUE')),
            ('skip', Bool()),
        ),
        dict_type=Pattern_v2_1_0,
    )

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            sql = """SELECT pattern, skip FROM patterns;"""
            p_list = []
            cursor = connection.cursor()
            for pattern, skip in db.execute(cursor, sql):
                p_list.append((Path.db_from(pattern), Bool.db_from(skip)))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', self.PATTERNS_TABLE_v2_0_x.fields, connection=connection)
            sql = """INSERT INTO patterns (pattern) VALUES (?);"""
            for pattern, skip in p_list:
                if not skip:
                    values = (Path.db_to(pattern), )
                    db.execute(cursor, sql, values)
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT pattern FROM patterns;"""
            p_list = []
            for pattern, in db.execute(cursor, sql):
                p_list.append(Path.db_from(pattern))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', self.PATTERNS_TABLE_v2_1_0.fields, connection=connection)
            values = []
            for p in p_list:
                values.append((Path.db_to(p), Bool.db_to(False)))
            sql = """INSERT INTO patterns (pattern, skip) VALUES (?, ?);"""
            db.execute(cursor, sql, *values)

