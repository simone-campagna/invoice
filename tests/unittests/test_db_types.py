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

from invoice.database.db_types import Str, StrList, StrTuple, \
                                      Int, IntList, IntTuple, \
                                      Float, FloatList, FloatTuple, \
                                      Date, DateList, DateTuple, \
                                      DateTime, DateTimeList, DateTimeTuple, \
                                      Path, PathList, PathTuple, \
                                      Bool, BoolList, BoolTuple, \
                                      OptionType, BaseSequence


class TestStr(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Str.db_from(None), None)
        self.assertEqual(Str.db_from("alpha"), "alpha")

    def test_db_to(self):
        self.assertIs(Str.db_to(None), None)
        self.assertEqual(Str.db_to("alpha"), "alpha")

class TestStrList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(StrList.db_from(None), None)
        self.assertEqual(StrList.db_from("alpha, beta, 10.3, gamma "), ["alpha", "beta", "10.3", "gamma"])

    def test_db_to(self):
        self.assertIs(StrList.db_to(None), None)
        self.assertEqual(StrList.db_to(["alpha", "beta", "10.3", "gamma"]), "alpha,beta,10.3,gamma")

class TestStrTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(StrTuple.db_from(None), None)
        self.assertEqual(StrTuple.db_from("alpha, beta, 10.3, gamma "), ("alpha", "beta", "10.3", "gamma"))

    def test_db_to(self):
        self.assertIs(StrTuple.db_to(None), None)
        self.assertEqual(StrTuple.db_to(("alpha", "beta", "10.3", "gamma")), "alpha,beta,10.3,gamma")

class TestInt(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Int.db_from(None), None)
        self.assertEqual(Int.db_from("10"), 10)

    def test_db_to(self):
        self.assertIs(Int.db_to(None), None)
        self.assertEqual(Int.db_to(10), "10")

class TestIntList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(IntList.db_from(None), None)
        self.assertEqual(IntList.db_from("10, 20"), [10, 20])

    def test_db_to(self):
        self.assertIs(IntList.db_to(None), None)
        self.assertEqual(IntList.db_to([10, 20]), "10,20")

class TestIntTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(IntTuple.db_from(None), None)
        self.assertEqual(IntTuple.db_from("10, 20"), (10, 20))

    def test_db_to(self):
        self.assertIs(IntTuple.db_to(None), None)
        self.assertEqual(IntTuple.db_to((10, 20)), "10,20")

class TestFloat(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Float.db_from(None), None)
        self.assertEqual(Float.db_from("10.5"), 10.5)

    def test_db_to(self):
        self.assertIs(Float.db_to(None), None)
        self.assertEqual(Float.db_to(10.5), "10.5")

class TestFloatList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(FloatList.db_from(None), None)
        self.assertEqual(FloatList.db_from("10.5,23.32"), [10.5, 23.32])

    def test_db_to(self):
        self.assertIs(FloatList.db_to(None), None)
        self.assertEqual(FloatList.db_to([10.5, 23.32]), "10.5,23.32")

class TestFloatTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(FloatTuple.db_from(None), None)
        self.assertEqual(FloatTuple.db_from("10.5,23.32"), (10.5, 23.32))

    def test_db_to(self):
        self.assertIs(FloatTuple.db_to(None), None)
        self.assertEqual(FloatTuple.db_to((10.5, 23.32)), "10.5,23.32")

class TestDate(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Date.db_from(None), None)
        self.assertEqual(Date.db_from("2015-01-04"), datetime.date(2015, 1, 4))

    def test_db_to(self):
        self.assertIs(Date.db_to(None), None)
        self.assertEqual(Date.db_to(datetime.date(2015, 1, 4)), "2015-01-04")

class TestDateList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateList.db_from(None), None)
        self.assertEqual(DateList.db_from(" 2015-01-04 , 2014-04-05 "), [datetime.date(2015, 1, 4), datetime.date(2014, 4, 5)])

    def test_db_to(self):
        self.assertIs(DateList.db_to(None), None)
        self.assertEqual(DateList.db_to([datetime.date(2015, 1, 4), datetime.date(2014, 4, 5)]), "2015-01-04,2014-04-05")

class TestDateTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateTuple.db_from(None), None)
        self.assertEqual(DateTuple.db_from(" 2015-01-04 , 2014-04-05 "), (datetime.date(2015, 1, 4), datetime.date(2014, 4, 5)))

    def test_db_to(self):
        self.assertIs(DateTuple.db_to(None), None)
        self.assertEqual(DateTuple.db_to((datetime.date(2015, 1, 4), datetime.date(2014, 4, 5))), "2015-01-04,2014-04-05")

class TestDateTime(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateTime.db_from(None), None)
        self.assertEqual(DateTime.db_from("2015-01-04 13:34:45"), datetime.datetime(2015, 1, 4, 13, 34, 45))

    def test_db_to(self):
        self.assertIs(DateTime.db_to(None), None)
        self.assertEqual(DateTime.db_to(datetime.datetime(2015, 1, 4, 13, 34, 45)), "2015-01-04 13:34:45")

class TestDateTimeList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateTimeList.db_from(None), None)
        self.assertEqual(DateTimeList.db_from("2015-01-04 13:34:45,2014-04-05 02:22:01"), [datetime.datetime(2015, 1, 4, 13, 34, 45), datetime.datetime(2014, 4, 5, 2, 22, 1)])

    def test_db_to(self):
        self.assertIs(DateTimeList.db_to(None), None)
        self.assertEqual(DateTimeList.db_to([datetime.datetime(2015, 1, 4, 13, 34, 45), datetime.datetime(2014, 4, 5, 2, 22, 1)]), "2015-01-04 13:34:45,2014-04-05 02:22:01")

class TestDateTimeTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(DateTimeTuple.db_from(None), None)
        self.assertEqual(DateTimeTuple.db_from("2015-01-04 13:34:45,2014-04-05 02:22:01"), (datetime.datetime(2015, 1, 4, 13, 34, 45), datetime.datetime(2014, 4, 5, 2, 22, 1)))

    def test_db_to(self):
        self.assertIs(DateTimeTuple.db_to(None), None)
        self.assertEqual(DateTimeTuple.db_to((datetime.datetime(2015, 1, 4, 13, 34, 45), datetime.datetime(2014, 4, 5, 2, 22, 1))), "2015-01-04 13:34:45,2014-04-05 02:22:01")

class TestPath(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(Path.db_from(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(Path.db_from("{}".format(f("alpha"))), f("alpha"))

    def test_db_to(self):
        self.assertIs(Path.db_to(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(Path.db_to("alpha"), f("alpha"))

class TestPathList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(PathList.db_from(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(PathList.db_from("{},/b/c,{}".format(f("alpha"), f("d/e"))), [f("alpha"), "/b/c", f("d/e")])

    def test_db_to(self):
        self.assertIs(PathList.db_to(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(PathList.db_to(["alpha", "/b/c", "d/e"]), "{},/b/c,{}".format(f("alpha"), f("d/e")))

class TestPathTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(PathTuple.db_from(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(PathTuple.db_from("{},/b/c,{}".format(f("alpha"), f("d/e"))), (f("alpha"), "/b/c", f("d/e")))

    def test_db_to(self):
        self.assertIs(PathTuple.db_to(None), None)
        f = lambda x: os.path.normpath(os.path.abspath(x))
        self.assertEqual(PathTuple.db_to(("alpha", "/b/c", "d/e")), "{},/b/c,{}".format(f("alpha"), f("d/e")))

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

class TestBoolList(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(BoolList.db_from(None), None)
        self.assertEqual(BoolList.db_from("True,True,False,False"), [True, True, False, False])

    def test_db_to(self):
        self.assertIs(BoolList.db_to(None), None)
        self.assertEqual(BoolList.db_to([True, True, False, False]), "True,True,False,False")

        with self.assertRaises(ValueError):
            BoolList.db_to("True,alpha")

class TestBoolTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(BoolTuple.db_from(None), None)
        self.assertEqual(BoolTuple.db_from("True,True,False,False"), (True, True, False, False))

    def test_db_to(self):
        self.assertIs(BoolTuple.db_to(None), None)
        self.assertEqual(BoolTuple.db_to((True, True, False, False)), "True,True,False,False")

        with self.assertRaises(ValueError):
            BoolTuple.db_to("True,alpha")

class MyOption(OptionType):
    OPTIONS = ("alpha", "beta", "gamma")

class MyOptionTuple(BaseSequence):
    SCALAR_TYPE = MyOption
    SEQUENCE_TYPE = tuple

class TestMyOption(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(MyOption.db_from(None), None)
        self.assertEqual(MyOption.db_from("alpha"), "alpha")
        with self.assertRaises(ValueError) as cm:
            self.assertEqual(MyOption.db_from("x"), "x")

    def test_db_to(self):
        self.assertIs(MyOption.db_to(None), None)
        self.assertEqual(MyOption.db_to("alpha"), "alpha")
        with self.assertRaises(ValueError) as cm:
            self.assertEqual(MyOption.db_to("x"), "x")

class TestMyOptionTuple(unittest.TestCase):
    def test_db_from(self):
        self.assertIs(MyOptionTuple.db_from(None), None)
        self.assertEqual(MyOptionTuple.db_from("alpha, beta, gamma "), ("alpha", "beta", "gamma"))
        with self.assertRaises(ValueError) as cm:
            self.assertEqual(MyOptionTuple.db_from("alpha, x, gamma "), ("alpha", "x", "gamma"))

    def test_db_to(self):
        self.assertIs(MyOptionTuple.db_to(None), None)
        self.assertEqual(MyOptionTuple.db_to(("alpha", "beta", "gamma")), "alpha,beta,gamma")
        with self.assertRaises(ValueError) as cm:
            self.assertEqual(MyOptionTuple.db_to(("alpha", "x", "gamma")), "alpha,x,gamma")

