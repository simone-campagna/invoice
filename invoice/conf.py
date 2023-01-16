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
    'LIST_FIELD_NAMES_SHORT',
    'LIST_FIELD_NAMES_LONG',
    'LIST_FIELD_NAMES_FULL',
    'LIST_FIELD_NAMES',
    'DEFAULT_LIST_FIELD_NAMES',
    'STATS_GROUP_YEAR',
    'STATS_GROUP_MONTH',
    'STATS_GROUP_WEEK',
    'STATS_GROUP_WEEKDAY',
    'STATS_GROUP_DAY',
    'STATS_GROUP_SERVICE',
    'STATS_GROUP_TASK',
    'STATS_GROUP_CLIENT',
    'STATS_GROUP_CITY',
    'STATS_GROUPS',
    'DEFAULT_STATS_GROUP',
    'STATS_MODE_SHORT',
    'STATS_MODE_LONG',
    'STATS_MODE_FULL',
    'STATS_MODES',
    'DEFAULT_STATS_MODE',
    'TABLE_MODE_TEXT',
    'TABLE_MODE_CSV',
    'TABLE_MODE_SCSV',
    'TABLE_MODE_XLSX',
    'TABLE_MODES',
    'DEFAULT_TABLE_MODE',
    'DEFAULT_MAX_INTERRUPTION_DAYS',
    'RC_DIR_VAR',
    'DB_FILE_VAR',
    'RC_DIR_EXPR',
    'DB_FILE_EXPR',
    'RC_DIR',
    'TMP_DOCS_DIR',
    'DB_FILE',
    'SCANNER_CONFIG_FILE',
    'PARSER_CONFIG_FILE',
    'WEEKDAY',
    'WEEKDAY_TRANSLATION',
    'WEEKDAY_TRANSLATION_DICT',
    'WEEKDAY_NUMBER',
    'MONTH_TRANSLATION_DICT',
    'MONTH',
    'MONTH_TRANSLATION',
    'setup',
    'get_rc_dir',
    'get_db_file',
    'get_scanner_config_file',
    'get_parser_config_file',
    'DEFAULT_EDITOR',
    'SPY_LOCK_FILE',
    'SPY_LOG_FILE',
    'SPY_NOTIFY_LEVEL_INFO',
    'SPY_NOTIFY_LEVEL_WARNING',
    'SPY_NOTIFY_LEVEL_ERROR',
    'SPY_NOTIFY_LEVELS',
    'DEFAULT_SPY_NOTIFY_LEVEL',
    'DEFAULT_SPY_DELAY',
    'DEFAULT_PROGRESSBAR',
    'ALIGN',
    'DERIVATIVES',
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
    ('service',		'prestazione'),
    ('fee',		'compenso'),
    ('refunds',		'rimborsi'),
    ('p_cpa',		'percentuale_cpa'),
    ('cpa',		'cpa'),
    ('p_vat',		'percentuale_iva'),
    ('vat',		'iva'),
    ('p_deduction',	'percentuale_ritenuta'),
    ('deduction',	'ritenuta'),
    ('taxes',		'bolli'),
    ('income',		'incasso'),
    ('currency',	'valuta'),
    ('exceptions',	'eccezioni'),
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
WEEKDAY_NUMBER = {}
for c, (weekday, weekday_translation) in enumerate(WEEKDAY_TRANSLATION_DICT.items()):
    WEEKDAY_NUMBER[weekday] = c
    WEEKDAY_NUMBER[weekday_translation] = c

MONTH_TRANSLATION_DICT = collections.OrderedDict((
    ('January',		'Gennaio'),
    ('February',	'Febbraio'),
    ('March',		'Marzo'),
    ('April',		'Aprile'),
    ('May',		'Maggio'),
    ('June',		'Giugno'),
    ('July',		'Luglio'),
    ('August',		'Agosto'),
    ('September',	'Settembre'),
    ('October',		'Ottobre'),
    ('November',	'Novembre'),
    ('December',	'Dicembre'),
))

MONTH = tuple(MONTH_TRANSLATION_DICT.keys())
MONTH_TRANSLATION = tuple(MONTH_TRANSLATION_DICT.values())

FIELD_NAMES = tuple(FIELD_TRANSLATION.keys())
REV_FIELD_TRANSLATION = dict(
    (FIELD_TRANSLATION.get(field_name, field_name), field_name) for field_name in FIELD_NAMES
)
LIST_FIELD_NAMES = FIELD_NAMES + tuple(REV_FIELD_TRANSLATION.keys())

LIST_FIELD_NAMES_SHORT = ('year', 'number', 'date', 'tax_code', 'income', 'currency')
LIST_FIELD_NAMES_LONG = ('year', 'number', 'city', 'date', 'tax_code', 'name', 'fee', 'refunds', 'cpa', 'taxes', 'income', 'currency', 'exceptions')
LIST_FIELD_NAMES_FULL = FIELD_NAMES

DEFAULT_LIST_FIELD_NAMES = LIST_FIELD_NAMES_LONG

STATS_MODE_SHORT = 'short'
STATS_MODE_LONG = 'long'
STATS_MODE_FULL = 'full'
STATS_MODES = (STATS_MODE_SHORT, STATS_MODE_LONG, STATS_MODE_FULL)
DEFAULT_STATS_MODE = STATS_MODE_LONG

STATS_GROUP_YEAR = 'year'
STATS_GROUP_MONTH = 'month'
STATS_GROUP_WEEK = 'week'
STATS_GROUP_DAY = 'day'
STATS_GROUP_WEEKDAY = 'weekday'
STATS_GROUP_SERVICE = 'service'
STATS_GROUP_TASK = 'task'
STATS_GROUP_CLIENT = 'client'
STATS_GROUP_CITY = 'city'
STATS_GROUPS = (STATS_GROUP_YEAR, STATS_GROUP_MONTH, STATS_GROUP_WEEK, STATS_GROUP_WEEKDAY, STATS_GROUP_DAY, STATS_GROUP_CLIENT, STATS_GROUP_CITY, STATS_GROUP_SERVICE, STATS_GROUP_TASK)
DEFAULT_STATS_GROUP = STATS_GROUP_MONTH

TABLE_MODE_TEXT = 'text'
TABLE_MODE_CSV = 'csv'
TABLE_MODE_SCSV = 'scsv'
TABLE_MODE_XLSX = 'xlsx'
TABLE_MODES = (TABLE_MODE_TEXT, TABLE_MODE_CSV, TABLE_MODE_SCSV, TABLE_MODE_XLSX)
DEFAULT_TABLE_MODE = TABLE_MODE_TEXT

DEFAULT_MAX_INTERRUPTION_DAYS = 365

VERSION_MAJOR = 3
VERSION_MINOR = 0
VERSION_PATCH = 0

VERSION = '{}.{}.{}'.format(VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

RC_DIR_VAR = 'INVOICE_RC_DIR'
DB_FILE_VAR = 'INVOICE_DB_FILE'

SCANNER_CONFIG_FILE = ""
PARSER_CONFIG_FILE = ""

INFO_CONFIG_FILE = ""

def setup(rc_dir=None, db_file=None):
    def expand(p):
        return os.path.expandvars(os.path.expanduser(p))
    global RC_DIR_EXPR
    global DB_FILE_EXPR
    global RC_DIR
    global TMP_DOCS_DIR
    global DB_FILE
    global SCANNER_CONFIG_FILE
    global PARSER_CONFIG_FILE
    global INFO_CONFIG_FILE
    global SPY_LOCK_FILE
    global SPY_LOG_FILE
    if rc_dir is None:
        rc_dir = os.path.join('~', '.invoice-db')
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

    TMP_DOCS_DIR = os.path.join(RC_DIR, 'tmp-docs')
    if not os.path.exists(TMP_DOCS_DIR):
        os.makedirs(TMP_DOCS_DIR)
    SCANNER_CONFIG_FILE = os.path.join(RC_DIR, "scanner.config")
    PARSER_CONFIG_FILE = os.path.join(RC_DIR, "parser.config")
    INFO_CONFIG_FILE = os.path.join(RC_DIR, "info.config")
    SPY_LOCK_FILE = os.path.join(RC_DIR, ".spy.lock")
    SPY_LOCK_FILE = os.path.join(RC_DIR, ".spy.lock")
    SPY_LOG_FILE = os.path.join(RC_DIR, "spy.log")

def get_rc_dir():
    return RC_DIR

def get_db_file():
    return DB_FILE

def get_scanner_config_file():
    return SCANNER_CONFIG_FILE

def get_parser_config_file():
    return PARSER_CONFIG_FILE

setup()

DEFAULT_EDITOR = os.environ.get("INVOICE_EDITOR", os.environ.get("EDITOR", "vim"))

SPY_NOTIFY_LEVEL_INFO = 'info'
SPY_NOTIFY_LEVEL_WARNING = 'warning'
SPY_NOTIFY_LEVEL_ERROR = 'error'
SPY_NOTIFY_LEVEL_NONE = 'none'
SPY_NOTIFY_LEVELS = (SPY_NOTIFY_LEVEL_INFO, SPY_NOTIFY_LEVEL_WARNING, SPY_NOTIFY_LEVEL_ERROR, SPY_NOTIFY_LEVEL_NONE)
SPY_NOTIFY_LEVEL_INDEX = dict((level, c) for c, level in enumerate(SPY_NOTIFY_LEVELS))
DEFAULT_SPY_NOTIFY_LEVEL = SPY_NOTIFY_LEVEL_INFO
DEFAULT_SPY_DELAY = 0.5
DEFAULT_PROGRESSBAR = True

ALIGN = {
    'number': '>',
    'income': '>',
    'fee': '>',
    'refunds': '>',
    'taxes': '>',
    'cpa': '>',
    'p_cpa': '>',
    'vat': '>',
    'p_vat': '>',
    'deduction': '>',
    'p_deduction': '>',
    'client_count': '>',
    'invoice_count': '>',
    'income_percentage': '>',
    'from': '>',
    'to': '>',
    'exceptions': '>',
}

DERIVATIVES = {
    'vat': ['fee', 'cpa', 'refunds'],
    'cpa': ['fee', 'refunds'],
    'deduction': ['fee', 'refunds'],
    'income': ['fee', 'refunds', 'cpa', 'vat', 'deduction', 'taxes'],
}
