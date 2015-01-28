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

import datetime
import re
import subprocess

from .invoice import Invoice
from .log import get_default_logger

class InvoiceReader(object):
    RE_INVOICE_NUMBER = re.compile("^[Ff]attura\s+n.\s+(?P<year>\d+)/(?P<number>\d+)\s*$")
    RE_NAME = re.compile("^\s*[Ss]pett\.(?:\s*[Ss]ig\.?)?\s*(?P<name>[\w\s'\.]+)\s*$")
    RE_TAX_CODE = re.compile("^.*[^\w](?P<tax_code>[A-Z]{6,6}\d{2,2}[A-Z]\d{2,2}[A-Z]\d{3,3}[A-Z])\s*$")
    RE_MALFORMED_TAX_CODE = re.compile("^.*[^\w](?P<tax_code>[A-Za-z0]{6,6}[\dO]{2,2}[A-Za-z0][\dO]{2,2}[A-Za-z0][\dO]{3,3}[A-Za-z0])\s*$")
    RE_DATE = re.compile("^\s*(?P<city>[^,]+)(?:,|\s)\s*(?P<date>\d{1,2}/\d{1,2}/\d\d\d\d)\s*$")
    RE_TOTAL = re.compile("Totale\s+fattura\s+(?P<income>[\d,\.]*)\s+(?P<currency>\w+)\s*$")
    DATE_FORMATS = (
        "%d/%m/%Y",
    )
    def __init__(self, logger):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        
    def __call__(self, doc_filename):
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
        for line in self.read_text(doc_filename).split('\n'):
            if not got_number:
                match = self.RE_INVOICE_NUMBER.match(line)
                if match:
                    got_number = True
                    store(data, converters, match)
                    continue
            if not got_name:
                match = self.RE_NAME.match(line)
                if match:
                    got_name = True
                    store(data, converters, match)
                    continue
            if not got_tax_code:
                match = self.RE_TAX_CODE.match(line)
                if match:
                    got_tax_code = True
                    store(data, converters, match)
                    continue
                match = self.RE_MALFORMED_TAX_CODE.match(line)
                if match:
                    store(data, converters, match)
                    continue
            if not got_date:
                match = self.RE_DATE.match(line)
                if match:
                    got_date = True
                    store(data, converters, match)
                    continue
            if not got_total:
                match = self.RE_TOTAL.match(line)
                if match:
                    got_total = True
                    store(data, converters, match)
                    continue
        invoice = Invoice(**data)
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
        
