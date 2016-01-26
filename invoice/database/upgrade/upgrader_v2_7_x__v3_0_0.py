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
    'Upgrader_v2_7_x__v3_0_0',
]

import collections
import sqlite3

from ..db_types import Bool, Str, StrTuple, Int, Float, Path, Date
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version
from ...validation_result import ValidationResult
from ... import conf

class Upgrader_v2_7_x__v3_0_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 7, None)
    VERSION_TO_MAJOR_MINOR = Version(3, 0, 0)
    INVOICES_TABLE_v2_7_x = DbTable(
        fields=(
                ('ID', Int('PRIMARY KEY')),
                ('doc_filename', Path('UNIQUE')),
                ('year', Int()),
                ('number', Int()),
                ('name', Str()),
                ('tax_code', Str()),
                ('city', Str()),
                ('date', Date()),
                ('service', Str()),
                ('income', Float()),
                ('currency', Str()),
        ),
    )
    INVOICES_TABLE_v3_0_0 = DbTable(
            fields=(
                ('ID', Int('PRIMARY KEY')),
                ('doc_filename', Path('UNIQUE')),
                ('year', Int()),
                ('number', Int()),
                ('name', Str()),
                ('tax_code', Str()),
                ('city', Str()),
                ('date', Date()),
                ('service', Str()),
                ('fee', Float()),
                ('refunds', Float()),
                ('p_cpa', Float()),
                ('cpa', Float()),
                ('p_vat', Float()),
                ('vat', Float()),
                ('p_deduction', Float()),
                ('deduction', Float()),
                ('taxes', Float()),
                ('income', Float()),
                ('currency', Str()),
            ),
    )

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        def new_to_old(new_data):
            return {}

        return self.do_downgrade(
            table_name="invoices",
            old_table=self.INVOICES_TABLE_v2_7_x,
            new_table=self.INVOICES_TABLE_v3_0_0,
            new_to_old=new_to_old,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
        with db.connect() as connection:
            cursor = connection.cursor()

    def impl_upgrade(self, db, version_from, version_to, connection=None):
        def old_to_new(old_data):
            return {
                'fee': old_data["income"],
                'refunds': 0.0,
                'taxes': 0.0,
                'p_cpa': 0.0,
                'cpa': 0.0,
                'p_vat': 0.0,
                'vat': 0.0,
                'p_deduction': 0.0,
                'deduction': 0.0,
            }
        self.do_upgrade(
            table_name="invoices",
            old_table=self.INVOICES_TABLE_v2_7_x,
            new_table=self.INVOICES_TABLE_v3_0_0,
            old_to_new=old_to_new,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
        with db.connect() as connection:
            cursor = connection.cursor()

