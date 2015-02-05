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
    'BaseType',
    'Str',
    'Int',
    'Float',
    'Date',
    'DateTime',
    'Path',
    'Bool',
    'BaseSequence',
    'StrList',
    'IntList',
    'FloatList',
    'BoolList',
    'PathList',
    'DateList',
    'DateTimeList',
    'StrTuple',
    'IntTuple',
    'FloatTuple',
    'BoolTuple',
    'PathTuple',
    'DateTuple',
    'DateTimeTuple',
]

import datetime
import os

class BaseType(object):
    DB_TYPENAME = None
    PY_TYPE = None
    def __init__(self, *db_create_args):
        self._db_create_args = db_create_args

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join(repr(arg) for arg in self._db_create_args))

    def db_create_args(self):
        return self._db_create_args

    @classmethod
    def db_typename(cls):
        return cls.DB_TYPENAME

    @classmethod
    def py_type(cls):
        return cls.PY_TYPE

    @classmethod
    def db_from(cls, value_s):
        if value_s is None:
            return None
        else:
            return cls.impl_db_from(value_s)

    @classmethod
    def db_to(cls, value):
        if value is None:
            return None
        else:
            return cls.impl_db_to(value)

    @classmethod
    def impl_db_from(cls, value_s):
        return cls.py_type()(value_s)

    @classmethod
    def impl_db_to(cls, value):
        return str(value)

class Str(BaseType):
    DB_TYPENAME = 'TEXT'
    PY_TYPE = str

class Path(Str):
    @classmethod
    def impl_db_to(cls, value):
        return os.path.normpath(os.path.abspath(value))

class Int(BaseType):
    DB_TYPENAME = 'INTEGER'
    PY_TYPE = int

class Float(BaseType):
    DB_TYPENAME = 'REAL'
    PY_TYPE = float

class Date(BaseType):
    DB_TYPENAME = 'TEXT'
    PY_TYPE = datetime.date
    DATE_FORMAT = "%Y-%m-%d"
    
    @classmethod
    def impl_db_from(cls, value_s):
        return datetime.datetime.strptime(value_s, cls.DATE_FORMAT).date()

    @classmethod
    def impl_db_to(cls, value):
        return value.strftime(cls.DATE_FORMAT)

class DateTime(BaseType):
    DB_TYPENAME = 'TEXT'
    PY_TYPE = datetime.date
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    @classmethod
    def impl_db_from(cls, value_s):
        return datetime.datetime.strptime(value_s, cls.DATETIME_FORMAT)

    @classmethod
    def impl_db_to(cls, value):
        return value.strftime(cls.DATETIME_FORMAT)

class Bool(BaseType):
    DB_TYPENAME = "INTEGER"
    PY_TYPE = bool

    @classmethod
    def fromstr(cls, value):
        if value == "True":
            return True
        elif value == "False":
            return False
        else:
            raise ValueError("{}: valore {!r} non valido (i valori leciti sono True|False)".format(cls.__name__, value, type(value).__name__))
    @classmethod
    def impl_db_from(cls, i):
        if isinstance(i, str):
            return cls.fromstr(i)
        else:
            return bool(i)

    @classmethod
    def impl_db_to(cls, value):
        if isinstance(value, str):
            return cls.fromstr(value)
        else:
            return bool(value)

class BaseSequence(BaseType):
    SEPARATOR = ','
    SCALAR_TYPE = BaseType
    SEQUENCE_TYPE = list

    @classmethod
    def impl_db_from(cls, s):
        return cls.SEQUENCE_TYPE(cls.SCALAR_TYPE.impl_db_from(v.strip()) for v in s.split(cls.SEPARATOR))

    @classmethod
    def impl_db_to(cls, l):
        return cls.SEPARATOR.join(str(cls.SCALAR_TYPE.impl_db_to(e)) for e in l)

class StrList(BaseSequence):
    SCALAR_TYPE = Str
    SEQUENCE_TYPE = list

class IntList(BaseSequence):
    SCALAR_TYPE = Int
    SEQUENCE_TYPE = list

class FloatList(BaseSequence):
    SCALAR_TYPE = Float
    SEQUENCE_TYPE = list

class BoolList(BaseSequence):
    SCALAR_TYPE = Bool
    SEQUENCE_TYPE = list

class PathList(BaseSequence):
    SCALAR_TYPE = Path
    SEQUENCE_TYPE = list

class DateList(BaseSequence):
    SCALAR_TYPE = Date
    SEQUENCE_TYPE = list

class DateTimeList(BaseSequence):
    SCALAR_TYPE = DateTime
    SEQUENCE_TYPE = list

class StrTuple(BaseSequence):
    SCALAR_TYPE = Str
    SEQUENCE_TYPE = tuple

class IntTuple(BaseSequence):
    SCALAR_TYPE = Int
    SEQUENCE_TYPE = tuple

class FloatTuple(BaseSequence):
    SCALAR_TYPE = Float
    SEQUENCE_TYPE = tuple

class BoolTuple(BaseSequence):
    SCALAR_TYPE = Bool
    SEQUENCE_TYPE = tuple

class PathTuple(BaseSequence):
    SCALAR_TYPE = Path
    SEQUENCE_TYPE = tuple

class DateTuple(BaseSequence):
    SCALAR_TYPE = Date
    SEQUENCE_TYPE = tuple

class DateTimeTuple(BaseSequence):
    SCALAR_TYPE = DateTime
    SEQUENCE_TYPE = tuple
