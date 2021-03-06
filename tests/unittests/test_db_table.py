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
    'TestTable',
]

import collections
import unittest

from invoice.database.db_table import DbTable
from invoice.database.db_types import Str, Float


_Invoice = collections.namedtuple("_Invoice", ("name", "income", "tax_code"))

class TestDbTable(unittest.TestCase):
    def setUp(self):
        pass

    def test_table0(self):
        t = DbTable(
            fields=(
                ('name',	Str()),
                ('income',	Float()),
                ('tax_code',	Str()),
            ),
        )

    def test_table1(self):
        t = DbTable(
            fields=(
                ('name',	Str()),
                ('income',	Float()),
                ('tax_code',	Str()),
            ),
            dict_type=_Invoice,
        )
