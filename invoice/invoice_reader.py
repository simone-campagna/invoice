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
    'InvoiceReader',
]

import collections
import datetime
import re
import subprocess

from .error import InvoiceDuplicatedLineError
from .invoice import Invoice
from .log import get_default_logger

class InvoiceReader(object):
    RE_YEAR_AND_NUMBER = re.compile("^[Ff]attura\s+n.\s+(?P<year>\d+)/(?P<number>\d+)\s*$")
    RE_NAME = re.compile("^\s*[Ss]pett\.\s*(?:[Ss]ig\.?|[Dd]ott\.?)?\s*(?P<name>[\w\s'\.]+)\s*$")
    RE_TAX_CODE = re.compile("^.*[^\w]?(?P<tax_code>[A-Z]{6,6}\d{2,2}[A-Z]\d{2,2}[A-Z]\d{3,3}[A-Z])\s*$")
    RE_MALFORMED_TAX_CODE = re.compile("^.*[^\w](?P<tax_code>[A-Za-z0]{6,6}[\dO]{2,2}[A-Za-z0][\dO]{2,2}[A-Za-z0][\dO]{3,3}[A-Za-z0])\s*$")
    RE_CITY_AND_DATE = re.compile("^\s*(?P<city>[^,]+)(?:,|\s)\s*(?P<date>\d{1,2}/\d{1,2}/\d\d\d\d)\s*$")
    RE_INCOME_AND_CURRENCY = re.compile("Totale\s+fattura\s+(?P<income>[\d,\.]*)\s+(?P<currency>\w+)\s*$")
    RE_DICT = collections.OrderedDict((
        ('year_and_number',	(None,		RE_YEAR_AND_NUMBER)),
        ('name',		(None,		RE_NAME)),
        ('tax_code',		(None,		RE_TAX_CODE)),
        ('malformed_tax_code',	('tax_code',	RE_MALFORMED_TAX_CODE)),
        ('city_and_date',	(None,		RE_CITY_AND_DATE)),
        ('income_and_currency',	(None,		RE_INCOME_AND_CURRENCY)),
    ))
    DATE_FORMATS = (
        "%d/%m/%Y",
    )
    def __init__(self, logger):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        
    def __call__(self, validation_result, doc_filename):
        got_number = False
        got_date = False
        got_name = False
        got_tax_code = False
        got_total = False
        data = {field: None for field in Invoice._fields}
        data['doc_filename'] = doc_filename
        converters = {
            'year': int,
            'number': int,
            'name': self.convert_name,
            'tax_code': self.convert_tax_code,
            'city': str,
            'date': self.convert_date,
            'income': self.convert_income,
            'currency': str,
        }
        malformed_tax_code = None
        def store(data, converters, match):
            data.update({key: converters[key](val) for key, val in match.groupdict().items()})
        tag_data = collections.OrderedDict()
        for line in self.read_text(doc_filename).split('\n'):
            for tag, (field_name, regex) in self.RE_DICT.items():
                if field_name is None:
                    field_name = tag
                match = regex.match(line)
                if match:
                    keys = {key: converters[key](val) for key, val in match.groupdict().items()}
                    tag_data.setdefault(tag, []).append((line, keys))

        if 'malformed_tax_code' in tag_data:
            if not 'tax_code' in tag_data:
                tag_data['tax_code'] = tag_data['malformed_tax_code']
            del tag_data['malformed_tax_code']

        postponed_errors = []
        for tag, entries in tag_data.items():
            if len(entries) > 1:
                message = "fattura {}: linee {!r} duplicate".format(doc_filename, tag)
                postponed_errors.append((
                    InvoiceDuplicatedLineError,
                    message))
                self.logger.error(message + ':')
                for line, keys in entries:
                    self.logger.error("  {}: {!r}".format(tag, line.strip()))
            line,keys = entries[0]
            data.update(keys)
        invoice = Invoice(**data)
        for exc_type, message in postponed_errors:
            validation_result.add_error(invoice, exc_type, message)
        self.logger.info("fattura {} letta con successo".format(invoice))
        return invoice

    @classmethod
    def convert_name(cls, income_s):
        return ' '.join(item.title() for item in income_s.split())

    @classmethod
    def convert_tax_code(cls, income_s):
        return income_s.strip()

    @classmethod
    def convert_income(cls, income_s):
        return float(income_s.replace('.', '').replace(',', '.'))

    @classmethod
    def convert_date(cls, date_s):
        for date_fmt in cls.DATE_FORMATS:
            try:
                datet = datetime.datetime.strptime(date_s, date_fmt)
            except ValueError as err:
                continue
            return datet.date()
        return None
           
    def read_text(self, doc_filename):
        cmdline = ["catdoc", doc_filename, "-f", "ascii", "-w"]
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.communicate()[0].decode("utf-8")
        
