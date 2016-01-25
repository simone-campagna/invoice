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
import os
import re
import subprocess

from .error import InvoiceDuplicatedLineError, InvoiceMissingDocFileError, \
    InvoiceKeyConversionError
from .invoice import Invoice
from .log import get_default_logger
from .scanner import Scanner, load_scanner
from . import conf

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

class InvoiceReader(object):
    DATE_FORMATS = (
        "%d/%m/%Y",
    )
    NULLABLE_FLOAT_FIELDS = ("p_vat", "vat", "p_deduction", "deduction", "extras", "refund")
    def __init__(self, logger=None):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        
    def __call__(self, validation_result, doc_filename):
        data = {field: None for field in Invoice._fields}
        postponed_errors = []
        if os.path.exists(doc_filename):
            data['doc_filename'] = doc_filename
            converters = {
                'year': int,
                'number': int,
                'name': self.convert_name,
                'tax_code': self.convert_tax_code,
                'city': str,
                'date': self.convert_date,
                'service': self.convert_service,
                'fee': self.convert_money,
                'refund': self.convert_money,
                'income': self.convert_money,
                'extras': self.convert_money,
                'p_cpa': float,
                'cpa': self.convert_money,
                'p_vat': float,
                'vat': self.convert_nullable_money,
                'p_deduction': float,
                'deduction': self.convert_nullable_money,
                'currency': str,
            }
            scanner = get_scanner()
            lines_dict, values_dict = scanner.scan(self.read_text(doc_filename))
            extra_keys = tuple(filter(lambda key: key.startswith("extra_"), values_dict.keys()))
            for key in self.NULLABLE_FLOAT_FIELDS:
                if key not in values_dict:
                    values_dict[key] = "0.0"
            for label, lines in lines_dict.items():
                if len(lines) > 1:
                    message = "fattura {}: linee {!r} duplicate".format(doc_filename, label)
                    postponed_errors.append((
                        InvoiceDuplicatedLineError,
                        message))
                    self.logger.error(message + ':')
                    for line in lines:
                        self.logger.error("  {}: {!r}".format(label, line.strip()))
                edict = {}
                for key, val in values_dict.items():
                    if key in extra_keys:
                        dummy_extra, to_key, extra_sub_key = key.split("_")
                        edict[key] = to_key
                    else:
                        to_key = key
                    if to_key in converters:
                        try:
                            val = converters[to_key](val)
                        except Exception as err:
                            message = "fattura {}: {}={!r}: {}: {}".format(
                                doc_filename, key, values_dict[key], type(err).__name__, err)
                            postponed_errors.append((InvoiceKeyConversionError, message))
                    data[key] = val
                for key in extra_keys:
                    to_key = edict[key]
                    data[edict[key]] += data[key]
                    del data[key]
                #data.update({key: converters[key](val) for key, val in values_dict.items()})
        else:
            postponed_errors.append((InvoiceMissingDocFileError, "fattura {}: doc file mancante".format(doc_filename)))
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
    def convert_money(cls, income_s):
        return float(income_s.replace('.', '').replace(',', '.'))

    @classmethod
    def convert_nullable_money(cls, income_s):
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
           
    @classmethod
    def convert_service(cls, service_s):
        l = [token.lower() for token in service_s.split()]
        l[0] = l[0].title()
        return ' '.join(l)

    def read_text(self, doc_filename):
        cmdline = ["catdoc", doc_filename, "-f", "ascii", "-w"]
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.communicate()[0].decode("utf-8")
        
