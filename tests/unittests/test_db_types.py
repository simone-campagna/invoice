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
    'TestInvoiceProgram',
]

import os
import datetime
import unittest

from invoice.database.db_types import Str, \
                                      Int, \
                                      Float, \
                                      Date, \
                                      DateTime, \
                                      Path, \
                                      Bool


class TestStr(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Str.db_from(None), None)
        self.assertEqual(Str.db_from("alpha"), "alpha")

    def test_db_to(self):
        self.assertIs(Str.db_to(None), None)
        self.assertEqual(Str.db_to("alpha"), "alpha")

class TestInt(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Int.db_from(None), None)
        self.assertEqual(Int.db_from("10"), 10)

    def test_db_to(self):
        self.assertIs(Int.db_to(None), None)
        self.assertEqual(Int.db_to(10), "10")

class TestFloat(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Float.db_from(None), None)
        self.assertEqual(Float.db_from("10.5"), 10.5)

    def test_db_to(self):
        self.assertIs(Float.db_to(None), None)
        self.assertEqual(Float.db_to(10.5), "10.5")

class TestDate(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Date.db_from(None), None)
        self.assertEqual(Date.db_from("2015-01-04"), datetime.date(2015, 1, 4))

    def test_db_to(self):
        self.assertIs(Date.db_to(None), None)
        self.assertEqual(Date.db_to(datetime.date(2015, 1, 4)), "2015-01-04")

class TestDateTime(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateTime.db_from(None), None)
        self.assertEqual(DateTime.db_from("2015-01-04 13:34:45"), datetime.datetime(2015, 1, 4, 13, 34, 45))

    def test_db_to(self):
        self.assertIs(DateTime.db_to(None), None)
        self.assertEqual(DateTime.db_to(datetime.datetime(2015, 1, 4, 13, 34, 45)), "2015-01-04 13:34:45")

class TestPath(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Path.db_from(None), None)
        self.assertEqual(Path.db_from("alpha"), "alpha")

    def test_db_to(self):
        self.assertIs(Path.db_to(None), None)
        self.assertEqual(Path.db_to("alpha"), os.path.normpath(os.path.abspath("alpha")))

class TestBool(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Bool.db_from(None), None)
        self.assertEqual(Bool.db_from(True), True)
        self.assertEqual(Bool.db_from(1), True)
        self.assertEqual(Bool.db_from(False), False)
        self.assertEqual(Bool.db_from(0), False)

    def test_db_to(self):
        self.assertIs(Bool.db_to(None), None)
        self.assertEqual(Bool.db_to("True"), True)
        self.assertEqual(Bool.db_to(1), True)
        self.assertEqual(Bool.db_to("False"), False)
        self.assertEqual(Bool.db_to(0), False)

        with self.assertRaises(ValueError):
            Bool.db_to("alpha")

