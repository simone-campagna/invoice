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
    'TestVersion',
]

import collections
import unittest

from invoice.version import Version


class TestVersion(unittest.TestCase):
    def setUp(self):
        self.va = Version(2, 0, 0)
        self.vb = Version(2, 0, 1)
        self.vc = Version(2, 1, 5)

        self.vx0 = Version(2, 0, 1)
        self.vy0 = Version(2, 0, 0)
        self.vz0 = Version(0, 0, 1)

        self.vx1 = Version(6, 4, 8)
        self.vy1 = Version(3, 3, 9)
        self.vz1 = Version(3, 1, -1)

    def test_eq(self):
        self.assertEqual(self.va, self.va)

    def test_ne(self):
        self.assertNotEqual(self.va, self.vb)

    def test_lt(self):
        self.assertLess(self.va, self.vb)
        self.assertLess(self.vb, self.vc)
        self.assertFalse(self.va < self.va)
        self.assertFalse(self.vb < self.va)

    def test_le(self):
        self.assertLessEqual(self.va, self.vb)
        self.assertLessEqual(self.vb, self.vc)
        self.assertTrue(self.va <= self.va)
        self.assertFalse(self.vb <= self.va)

    def test_gt(self):
        self.assertGreater(self.vb, self.va)
        self.assertGreater(self.vc, self.vb)
        self.assertFalse(self.va > self.va)
        self.assertFalse(self.va > self.vb)

    def test_ge(self):
        self.assertGreaterEqual(self.vb, self.va)
        self.assertGreaterEqual(self.vc, self.vb)
        self.assertTrue(self.va >= self.va)
        self.assertFalse(self.va >= self.vb)

    def test_sub(self):
        self.assertEqual(self.vx0 - self.vy0, self.vz0)
        self.assertEqual(self.vx1 - self.vy1, self.vz1)

    def test_add(self):
        self.assertEqual(self.vy0 + self.vz0, self.vx0)
        self.assertEqual(self.vy1 + self.vz1, self.vx1)

    def test_str(self):
        self.assertEqual(str(Version(3, 9, 2)), "3.9.2")
