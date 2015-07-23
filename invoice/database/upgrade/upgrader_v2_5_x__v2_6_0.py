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
from ...validation_result import ValidationResult
from ... import conf

class Upgrader_v2_5_x__v2_6_0(MajorMinorUpgrader):
    VERSION_FROM_MAJOR_MINOR = Version(2, 5, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 6, 0)

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        db.logger.warning("clearing invoices table...")
        with db.connect(connection) as connection:
            db.clear('invoices', connection=connection)

    def impl_upgrade(self, db, version_from, version_to, connection=None):
        db.logger.warning("clearing invoices table...")
        with db.connect(connection) as connection:
            db.clear('invoices', connection=connection)
