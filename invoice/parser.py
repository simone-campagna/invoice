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
    'Parser',
    'load_parser',
]

import collections
import configparser
import datetime
import inspect
import os

from . import conf
from .error import InvoiceDuplicatedLineError, InvoiceKeyConversionError
from .log import get_default_logger
from .files import create_file_dir
from .scanner import Scanner, load_scanner


_UNDEFINED = "__undefined__"

SCANNER = None
SCANNER_CONFIG_FILE = None
def get_scanner():
    global SCANNER
    global SCANNER_CONFIG_FILE
    scanner_config_file = conf.get_scanner_config_file()
    if SCANNER is None or SCANNER_CONFIG_FILE != scanner_config_file:
        SCANNER = load_scanner(scanner_config_file)
        SCANNER_CONFIG_FILE = scanner_config_file
    return SCANNER


class ParserMeta(type):
    def __new__(mcls, class_name, class_bases, class_dict):
        type_dict = collections.OrderedDict()
        action_dict = collections.OrderedDict()
        class_dict['TYPE'] = type_dict
        class_dict['ACTION'] = action_dict
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        type_prefix = "type_"
        action_prefix = "action_"
        for name, kind, objtype, obj in inspect.classify_class_attrs(cls):
            if kind == "class method":
                if name.startswith(type_prefix):
                    type_dict[name[len(type_prefix):]] = obj
                elif name.startswith(action_prefix):
                    action_dict[name[len(action_prefix):]] = obj
        return cls
 
class Parser(metaclass=ParserMeta):
    DATE_FORMATS = (
        "%d/%m/%Y",
    )
    _UNDEF = object()
    def __init__(self, logger=None):
        self._scanner = get_scanner()
        self._dict = {}
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        self._defaults = {}

    def add(self, entry, e_type="str", e_action="store", e_default=_UNDEFINED):
        try:
            m_type = getattr(self, "type_" + e_type)
        except:
            raise KeyError("undefined type {!r}".format(e_type))
        try:
            m_action = getattr(self, "action_" + e_action)
        except:
            raise KeyError("undefined action {!r}".format(e_action))
        self._dict[entry] = (m_type, m_action)
        if e_default != _UNDEFINED:
            value = m_type(e_default)
            self._defaults[entry] = value
        else:
            self._defaults[entry] = None

    @classmethod
    def type_str(cls, value):
        return value

    @classmethod
    def type_name(cls, value):
        return ' '.join(item.title() for item in value.split())

    @classmethod
    def type_int(cls, value):
        return int(value)

    @classmethod
    def type_float(cls, value):
        return float(value)

    @classmethod
    def type_money(cls, value):
        return float(value.replace('.', '').replace(',', '.'))

    @classmethod
    def type_tax_code(cls, value):
        return value.strip()

    @classmethod
    def type_date(cls, value):
        for date_fmt in cls.DATE_FORMATS:
            try:
                datet = datetime.datetime.strptime(value, date_fmt)
            except ValueError as err:
                continue
            return datet.date()
        return None

    @classmethod
    def type_service(cls, value):
        return ' '.join(value.split())

    @classmethod
    def convert(cls, *, logger, postponed_errors, m_type, lines_dict, line_no, value):
        try:
            return m_type(value)
        except Exception as err:
            e_type = m_type.__name__[len("type_"):]
            message = "{}: errore nella conversione a tipo {}".format(key, e_type)
            postponed_errors.append((InvoiceKeyConversionError, message))

    @classmethod
    def action_store(cls, *, logger, postponed_errors, m_type, lines_dict, key, lvalues):
        if len(lvalues) > 1:
            message = "{}: #{} linee duplicate".format(key, len(lvalues))
            postponed_errors.append((
                InvoiceDuplicatedLineError,
                message))
            logger.error(message + ':')
            for line_no, dummy_value in lvalues:
                logger.error("  {}: {!r}".format(key, lines_dict[line_no].strip()))
        line_no, value = lvalues[-1]
        return cls.convert(logger=logger, postponed_errors=postponed_errors, m_type=m_type, lines_dict=lines_dict, line_no=line_no, value=value)

    @classmethod
    def action_overwrite(cls, *, logger, postponed_errors, m_type, lines_dict, key, lvalues):
        line_no, value = lvalues[-1]
        return cls.convert(logger=logger, postponed_errors=postponed_errors, m_type=m_type, lines_dict=lines_dict, line_no=line_no, value=value)

    @classmethod
    def action_cumulate(cls, *, logger, postponed_errors, m_type, lines_dict, key, lvalues):
        values = []
        for line_no, value in lvalues:
            values.append(cls.convert(logger=logger, postponed_errors=postponed_errors, m_type=m_type, lines_dict=lines_dict, line_no=line_no, value=value))
        return sum(values)

    def parse(self, postponed_errors, document):
        values = self._defaults.copy()
        values_dict, lines_dict = self._scanner.scan(document)
        for key, lvalues in values_dict.items():
            m_type, m_action = self._dict[key]
            values[key] = m_action(logger=self.logger, postponed_errors=postponed_errors, m_type=m_type, lines_dict=lines_dict, key=key, lvalues=lvalues)
        return values


_DCT = {}
for _prefix, _dct in ("t_", Parser.TYPE), ("a_", Parser.ACTION):
    for _key in _dct.keys():
        _DCT[_prefix + _key] = _key


_DEFAULT_PARSER_CONFIG = """\
[DEFAULT]
type = {t_str}
action = {a_store}
default = {undefined}

[year]
type = {t_int}

[number]
type = {t_int}

[date]
type = {t_date}

[name]
type = {t_name}

[tax_code]
type = {t_tax_code}

[city]
type = {t_str}

[income]
type = {t_money}

[currency]
type = {t_str}

[service]
type = {t_service}

[fee]
type = {t_money}

[refunds]
type = {t_money}
action = {a_cumulate}
default = 0.0

[p_cpa]
type = {t_float}

[cpa]
type = {t_money}

[p_vat]
type = {t_float}
default = 0.0

[vat]
type = {t_money}
default = 0.0

[p_deduction]
type = {t_float}
default = 0.0

[deduction]
type = {t_money}
default = 0.0

[taxes]
type = {t_money}
action = {a_cumulate}
default = 0.0

""".format(undefined=_UNDEFINED, **_DCT)

def load_parser(parser_config_filename=None):
    if parser_config_filename is None:
        parser_config_filename = conf.get_parser_config_file()
    if not os.path.exists(parser_config_filename):
        create_file_dir(parser_config_filename)
        with open(parser_config_filename, "w") as f_out:
            f_out.write(_DEFAULT_PARSER_CONFIG)

    config = configparser.ConfigParser(interpolation=None)
    config.read(parser_config_filename)
    parser = Parser()
    for section_name in config.sections():
        section = config[section_name]
        entry = section_name
        dct = {}
        dct["e_type"] = section['type']
        dct["e_action"] = section['action']
        if "default" in section:
            dct["e_default"] = section["default"]
        parser.add(entry=entry, **dct)
    return parser

