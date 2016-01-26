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

from .error import InvoiceMissingDocFileError
from .invoice import Invoice
from .log import get_default_logger
from .parser import Parser, load_parser
from . import conf

PARSER = None
PARSER_CONFIG_FILE = None
def get_parser():
    global PARSER
    global PARSER_CONFIG_FILE
    parser_config_file = conf.get_parser_config_file()
    if PARSER is None or PARSER_CONFIG_FILE != parser_config_file:
        PARSER = load_parser(parser_config_file)
        PARSER_CONFIG_FILE = parser_config_file
    return PARSER

class InvoiceReader(object):
    def __init__(self, logger=None):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        self.parser = get_parser()
        
    def __call__(self, validation_result, doc_filename):
        postponed_errors = []
        if os.path.exists(doc_filename):
            document = self.read_text(doc_filename)
            values = self.parser.parse(postponed_errors, document)
        else:
            values = {key: None for key in Invoice._fields}
            postponed_errors.append((InvoiceMissingDocFileError, "doc file mancante"))
        values["doc_filename"] = doc_filename
        invoice = Invoice(**values)
        if postponed_errors:
            header = "fattura {}: ".format(doc_filename)
            for exc_type, message in postponed_errors:
                validation_result.add_error(invoice, exc_type, header + message)
            self.logger.error("fattura {} letta con #{} errori!".format(invoice, len(postponed_errors)))
        else:
            self.logger.info("fattura {} letta con successo".format(invoice))
        return invoice

    def read_text(self, doc_filename):
        cmdline = ["catdoc", doc_filename, "-f", "ascii", "-w"]
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.communicate()[0].decode("utf-8")
        
