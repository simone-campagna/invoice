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
    'Upgrader_v2_3_x__v2_4_0',
]

import collections

from ..db_types import Bool, Str, StrTuple
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version
from ... import conf

class Upgrader_v2_3_x__v2_4_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 3, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 4, 0)
    CONFIGURATION_TABLE_v2_3_x = DbTable(
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
    )
    CONFIGURATION_TABLE_v2_4_0 = DbTable(
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
        ),
    )
    def impl_downgrade(self, db, version_from, version_to, connection=None):
        return self.do_downgrade(
            old_table=self.CONFIGURATION_TABLE_v2_3_x,
            new_table=self.CONFIGURATION_TABLE_v2_4_0,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        return self.do_upgrade(
            old_table=self.CONFIGURATION_TABLE_v2_3_x,
            new_table=self.CONFIGURATION_TABLE_v2_4_0,
            new_data={'table_mode': conf.DEFAULT_TABLE_MODE},
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )
