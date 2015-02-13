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
    'VERSION_MAJOR',
    'VERSION_MINOR',
    'VERSION_PATCH',
    'VERSION',
    'FIELD_NAMES',
    'FIELD_TRANSLATION',
    'REV_FIELD_TRANSLATION',
    'ALL_FIELDS',
    'LIST_FIELD_NAMES_SHORT',
    'LIST_FIELD_NAMES_LONG',
    'LIST_FIELD_NAMES_FULL',
    'DEFAULT_LIST_FIELD_NAMES',
    'STATS_GROUP_YEAR',
    'STATS_GROUP_MONTH',
    'STATS_GROUP_WEEK',
    'STATS_GROUP_WEEKDAY',
    'STATS_GROUP_DAY',
    'STATS_GROUP_CLIENT',
    'STATS_GROUP_CITY',
    'STATS_GROUPS',
    'DEFAULT_STATS_GROUP',
    'RC_DIR_VAR',
    'DB_FILE_VAR',
    'RC_DIR_EXPR',
    'DB_FILE_EXPR',
    'RC_DIR',
    'DB_FILE',
    'SCANNER_CONFIG_FILE',
    'WEEKDAY',
    'WEEKDAY_TRANSLATION',
    'WEEKDAY_TRANSLATION_DICT',
    'setup',
    'get_rc_dir',
    'get_db_file',
    'get_scanner_config_file',
]

import collections
import os


FIELD_TRANSLATION = collections.OrderedDict((
    ('doc_filename',	'documento'),
    ('year', 		'anno'),
    ('number',		'numero'),
    ('name',		'nome'),
    ('tax_code',	'codice_fiscale'),
    ('city',		'città'),
    ('date',		'data'),
    ('income',		'importo'),
    ('currency',	'valuta'),
))

WEEKDAY_TRANSLATION_DICT = collections.OrderedDict((
    ('Monday',		'Lunedì'),
    ('Tuesday',		'Martedì'),
    ('Wednesday',	'Mercoledì'),
    ('Thursday',	'Giovedì'),
    ('Friday',		'Venerdì'),
    ('Saturday',	'Sabato'),
    ('Sunday',		'Domenica'),
))

WEEKDAY = tuple(WEEKDAY_TRANSLATION_DICT.keys())
WEEKDAY_TRANSLATION = tuple(WEEKDAY_TRANSLATION_DICT.values())
FIELD_NAMES = tuple(FIELD_TRANSLATION.keys())
REV_FIELD_TRANSLATION = dict(
    (FIELD_TRANSLATION.get(field_name, field_name), field_name) for field_name in FIELD_NAMES
)
ALL_FIELDS = FIELD_NAMES + tuple(REV_FIELD_TRANSLATION.keys())

LIST_FIELD_NAMES_SHORT = ('year', 'number', 'date', 'tax_code', 'income', 'currency')
LIST_FIELD_NAMES_LONG = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'income', 'currency')
LIST_FIELD_NAMES_FULL = FIELD_NAMES
DEFAULT_LIST_FIELD_NAMES = LIST_FIELD_NAMES_LONG


STATS_GROUP_YEAR = 'year'
STATS_GROUP_MONTH = 'month'
STATS_GROUP_WEEK = 'week'
STATS_GROUP_DAY = 'day'
STATS_GROUP_WEEKDAY = 'weekday'
STATS_GROUP_CLIENT = 'client'
STATS_GROUP_CITY = 'city'
STATS_GROUPS = (STATS_GROUP_YEAR, STATS_GROUP_MONTH, STATS_GROUP_WEEK, STATS_GROUP_WEEKDAY, STATS_GROUP_DAY, STATS_GROUP_CLIENT, STATS_GROUP_CITY)
DEFAULT_STATS_GROUP = STATS_GROUP_MONTH

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0

VERSION = '{}.{}.{}'.format(VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

RC_DIR_VAR = 'INVOICE_RC_DIR'
DB_FILE_VAR = 'INVOICE_DB_FILE'

SCANNER_CONFIG_FILE = ""

def setup(rc_dir=None, db_file=None):
    def expand(p):
        return os.path.expandvars(os.path.expanduser(p))
    global RC_DIR_EXPR
    global DB_FILE_EXPR
    global RC_DIR
    global DB_FILE
    global SCANNER_CONFIG_FILE
    if rc_dir is None:
        rc_dir = os.path.join('~', '.invoice')
    RC_DIR_EXPR = os.environ.get(RC_DIR_VAR, rc_dir)
    RC_DIR = expand(RC_DIR_EXPR)
    if not os.path.isabs(RC_DIR):
        RC_DIR = os.path.abspath(RC_DIR)

    if db_file is None:
        db_file = os.path.join(RC_DIR, "invoices.db")
    else:
        db_file = expand(db_file)
    DB_FILE_EXPR = os.environ.get(DB_FILE_VAR, db_file)
    DB_FILE = expand(DB_FILE_EXPR)
    if not os.path.isabs(DB_FILE):
        DB_FILE = os.path.join(RC_DIR, DB_FILE)

    SCANNER_CONFIG_FILE = os.path.join(RC_DIR, "scanner.config")

def get_rc_dir():
    return RC_DIR

def get_db_file():
    return DB_FILE

def get_scanner_config_file():
    return SCANNER_CONFIG_FILE

setup()

