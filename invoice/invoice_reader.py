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
from .scanner import Scanner, ScanLine


class InvoiceReader(object):
    RE_YEAR_AND_NUMBER = "^[Ff]attura\s+n.\s+(?P<year>\d+)/(?P<number>\d+)\s*$"
    RE_NAME = "^\s*[Ss]pett\.\s*(?:[Ss]ig\.?|[Dd]ott\.?)?\s*(?P<name>[\w\s'\.]+)\s*$"
    RE_TAX_CODE = "^.*[^\w]?(?P<tax_code>[A-Z]{6,6}\d{2,2}[A-Z]\d{2,2}[A-Z]\d{3,3}[A-Z])\s*$"
    RE_MALFORMED_TAX_CODE = "^.*[^\w](?P<tax_code>[A-Za-z0]{6,6}[\dO]{2,2}[A-Za-z0][\dO]{2,2}[A-Za-z0][\dO]{3,3}[A-Za-z0])\s*$"
    RE_CITY_AND_DATE = "^\s*(?P<city>[^,]+)(?:,|\s)\s*(?P<date>\d{1,2}/\d{1,2}/\d\d\d\d)\s*$"
    RE_INCOME_AND_CURRENCY = "Totale\s+fattura\s+(?P<income>[\d,\.]*)\s+(?P<currency>\w+)\s*$"
    SCANNER = Scanner((
        ScanLine(tag='year_and_number', regexpr=RE_YEAR_AND_NUMBER),
        ScanLine(tag='name', regexpr=RE_NAME),
        ScanLine(tag='tax_code', regexpr=RE_TAX_CODE),
        ScanLine(tag='malformed_tax_code', regexpr=RE_MALFORMED_TAX_CODE, priority=-1),
        ScanLine(tag='city_and_date', regexpr=RE_CITY_AND_DATE),
        ScanLine(tag='income_and_currency', regexpr=RE_INCOME_AND_CURRENCY),
    ))

    CRE_YEAR_AND_NUMBER = re.compile(RE_YEAR_AND_NUMBER)
    CRE_NAME = re.compile(RE_NAME)
    CRE_TAX_CODE = re.compile(RE_TAX_CODE)
    CRE_MALFORMED_TAX_CODE = re.compile(RE_MALFORMED_TAX_CODE)
    CRE_CITY_AND_DATE = re.compile(RE_CITY_AND_DATE)
    CRE_INCOME_AND_CURRENCY = re.compile(RE_INCOME_AND_CURRENCY)
    CRE_DICT = collections.OrderedDict((
        ('year_and_number',	(None,		CRE_YEAR_AND_NUMBER)),
        ('name',		(None,		CRE_NAME)),
        ('tax_code',		(None,		CRE_TAX_CODE)),
        ('malformed_tax_code',	('tax_code',	CRE_MALFORMED_TAX_CODE)),
        ('city_and_date',	(None,		CRE_CITY_AND_DATE)),
        ('income_and_currency',	(None,		CRE_INCOME_AND_CURRENCY)),
    ))
    DATE_FORMATS = (
        "%d/%m/%Y",
    )
    def __init__(self, logger):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        
    def __call__(self, validation_result, doc_filename):
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
        lines_dict, values_dict = self.SCANNER.scan(self.read_text(doc_filename))
        postponed_errors = []
        for label, lines in lines_dict.items():
            if len(lines) > 1:
                message = "fattura {}: linee {!r} duplicate".format(doc_filename, label)
                postponed_errors.append((
                    InvoiceDuplicatedLineError,
                    message))
                self.logger.error(message + ':')
                for line in lines:
                    self.logger.error("  {}: {!r}".format(label, line.strip()))
            data.update({key: converters[key](val) for key, val in values_dict.items()})

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
        
