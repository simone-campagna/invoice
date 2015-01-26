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
    'InvoiceProgram'
]

import os
import traceback

from .invoice_collection_reader import InvoiceCollectionReader
from .invoice_db import InvoiceDb

class InvoiceProgram(object):
    def __init__(self, db_filename, logger, print_function=print, trace=False):
        self.db_filename = db_filename
        self.logger = logger
        self.print_function = print_function
        self.trace = trace
        self.db = InvoiceDb(self.db_filename, self.logger)

    def db_init(self, *, patterns, reset, partial_update, remove_orphaned):
        if reset and os.path.exists(self.db_filename):
            self.logger.info("removing db {!r}".format(self.db_filename))
            os.remove(self.db_filename)
        self.db.initialize()
        self.db.configure(
            patterns=patterns,
            remove_orphaned=remove_orphaned,
            partial_update=partial_update,
        )
       

    def db_config(self, *, patterns, show, partial_update, remove_orphaned):
        new_patterns = []
        del_patterns = []
        for sign, pattern in patterns:
            if sign == '+':
                new_patterns.append(self.db.Pattern(pattern=pattern))
            elif sign == '-':
                del_patterns.append(self.db.Pattern(pattern=pattern))
        if new_patterns:
            self.db.write('patterns', new_patterns)
        if del_patterns:
            for pattern in del_patterns:
                self.db.delete('patterns', "pattern == {!r}".format(pattern.pattern))
        self.db.configure(
                patterns=None,
                remove_orphaned=remove_orphaned,
                partial_update=partial_update,
            )
        if show:
            self.db.show_configuration(print_function=self.print_function)

    def db_scan(self, *, warnings_mode, raise_on_error, partial_update, remove_orphaned):
        self.db.check()
        invoice_collection = self.db.scan(
            warnings_mode=warnings_mode,
            raise_on_error=raise_on_error,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )

    def db_clear(self):
        self.db.check()
        self.db.delete('invoices')

    def db_validate(self, *, warnings_mode, raise_on_error):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        validation_result = invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
        return validation_result.num_errors()

    def db_filter(self, invoice_collection, filters):
        self.db.check()
        if filters:
            self.logger.info("filtering {} invoices...".format(len(invoice_collection)))
            for filter_source in filters:
                self.logger.info("applying filter {!r} to {} invoices...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        return invoice_collection

    def db_list(self, *, field_names, header, filters):
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        invoice_collection.list(header=header, field_names=field_names, print_function=self.print_function)

    def db_dump(self, *, filters):
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        invoice_collection.dump(print_function=self.print_function)

    def db_report(self):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        invoice_collection.report(print_function=self.print_function)

    def legacy(self, patterns, filters, validate, list, report, warnings_mode, raise_on_error):
        invoice_collection_reader = InvoiceCollectionReader(trace=self.trace)

        invoice_collection = invoice_collection_reader(*patterns)

        if validate is None:
            validate = any([report])

        try:
            if validate:
                self.logger.info("validating {} invoices...".format(len(invoice_collection)))
                validation_result = invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
                if validation_result.num_errors():
                    self.logger.error("found #{} errors - exiting".format(validation_result.num_errors()))
                    return 1
    
            invoice_collection = self.db_filter(invoice_collection, filters)
    
            if list:
                self.logger.info("listing {} invoices...".format(len(invoice_collection)))
                invoice_collection.dump()
    
            if report:
                self.logger.info("producing report for {} invoices...".format(len(invoice_collection)))
                invoice_collection.report()
    
        except Exception as err:
            if self.trace:
                traceback.print_exc()
            self.logger.error("{}: {}\n".format(type(err).__name__, err))
