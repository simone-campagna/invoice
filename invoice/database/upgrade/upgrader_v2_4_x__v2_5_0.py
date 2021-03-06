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
    'Upgrader_v2_4_x__v2_5_0',
]

import collections

from ..db_types import Bool, Str, StrTuple, Int
from ..db_table import DbTable

from .upgrader import MajorMinorUpgrader

from ...version import Version
from ...validation_result import ValidationResult
from ... import conf

class Upgrader_v2_4_x__v2_5_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 4, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 5, 0)
    CONFIGURATION_TABLE_v2_4_x = DbTable(
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
    CONFIGURATION_TABLE_v2_5_0 = DbTable(
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

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        def new_to_old(new_data):
            return {
                'max_interruption_days': conf.DEFAULT_MAX_INTERRUPTION_DAYS,
                'warning_mode': ValidationResult.DEFAULT_WARNING_MODE,
                'error_mode': ValidationResult.DEFAULT_ERROR_MODE,
            }
        return self.do_downgrade(
            table_name="configuration",
            old_table=self.CONFIGURATION_TABLE_v2_4_x,
            new_table=self.CONFIGURATION_TABLE_v2_5_0,
            new_to_old=new_to_old,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )

    def impl_upgrade(self, db, version_from, version_to, connection=None):
        def old_to_new(old_data):
            return {
                'max_interruption_days': conf.DEFAULT_MAX_INTERRUPTION_DAYS,
                'warning_mode': ("{}:*".format(old_data['warning_mode']), ),
                'error_mode': ("{}:*".format(old_data['error_mode']), ),
            }
        return self.do_upgrade(
            table_name="configuration",
            old_table=self.CONFIGURATION_TABLE_v2_4_x,
            new_table=self.CONFIGURATION_TABLE_v2_5_0,
            old_to_new=old_to_new,
            db=db,
            version_from=version_from,
            version_to=version_to,
            connection=connection
        )

