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
    'InvoiceCollection',
]

import glob
import traceback

from .invoice_reader import InvoiceReader
from .invoice_collection import InvoiceCollection
from .log import get_default_logger
from .week import WeekManager

class InvoiceCollectionReader(object):
    def __init__(self, trace=False, logger=None):
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        self.trace = trace

    def __call__(self, *doc_filename_patterns):
        invoice_reader = InvoiceReader(logger=self.logger)
        invoice_collection = InvoiceCollection(logger=self.logger)
        for doc_filename_pattern in doc_filename_patterns:
            for doc_filename in glob.glob(doc_filename_pattern):
                try:
                    invoice_collection.add(invoice_reader(doc_filename))
                except Exception as err:
                    if self.trace:
                        traceback.print_exc()
                    self.logger.error("fattura {!r}: {}: {}".format(doc_filename, type(err).__name__, err))
        return invoice_collection
          

