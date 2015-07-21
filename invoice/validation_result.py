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
    'ValidationResult',
]

import collections

class ValidationResult(object):
    WARNING_MODE_LOG = 'log'
    WARNING_MODE_ERROR = 'error'
    WARNING_MODE_IGNORE = 'ignore'
    WARNING_MODES = (WARNING_MODE_LOG, WARNING_MODE_ERROR, WARNING_MODE_IGNORE)
    DEFAULT_WARNING_MODE = WARNING_MODE_LOG

    ERROR_MODE_LOG = 'log'
    ERROR_MODE_IGNORE = 'ignore'
    ERROR_MODE_RAISE = 'raise'
    ERROR_MODES = (ERROR_MODE_LOG, ERROR_MODE_IGNORE, ERROR_MODE_RAISE)
    DEFAULT_ERROR_MODE = ERROR_MODE_LOG

    Entry = collections.namedtuple('Entry', ('exc_type', 'message'))
    def __init__(self, logger, warning_mode=DEFAULT_WARNING_MODE, error_mode=DEFAULT_ERROR_MODE,
                               warning_suppression=None, error_suppression=None):
        self._failing_invoices = dict()
        self.logger = logger
        self._errors = collections.OrderedDict()
        self._warnings = collections.OrderedDict()

        if error_mode is None: # pragma: no cover
            error_mode = self.DEFAULT_ERROR_MODE

        if error_mode == self.ERROR_MODE_LOG:
            self._function_error = self.impl_add_error
        elif error_mode == self.ERROR_MODE_RAISE:
            self._function_error = self.impl_add_critical
        elif error_mode == self.ERROR_MODE_IGNORE:
            self._function_error = self.impl_ignore
        else: # pragma: no cover
            raise ValueError("error_mode {!r} non valido (i valori leciti sono {})".format(error_mode, '|'.join(self.ERROR_MODES)))
          
        if warning_mode is None: # pragma: no cover
            warning_mode = self.DEFAULT_WARNING_MODE

        if warning_mode == self.WARNING_MODE_LOG:
            self._function_warning = self.impl_add_warning
        elif warning_mode == self.WARNING_MODE_ERROR:
            self._function_warning = self._function_error
        elif warning_mode == self.WARNING_MODE_IGNORE:
            self._function_warning = self.impl_ignore
        else: # pragma: no cover
            raise ValueError("warning_mode {!r} non valido (i valori leciti sono {})".format(warning_mode, '|'.join(self.WARNING_MODES)))

        self.warning_mode = warning_mode
        self.error_mode = error_mode

        if error_suppression is None:
            error_suppression = ()
        self.error_suppression = set(error_suppression)

        if warning_suppression is None:
            warning_suppression = ()
        self.warning_suppression = set(warning_suppression)

    def filter_invoices(self, invoices):
        validated_invoices = []
        failing_invoices = []
        for invoice in invoices:
            if invoice.doc_filename in self._failing_invoices:
                failing_invoices.append(invoice)
            else:
                validated_invoices.append(invoice)
        return validated_invoices, failing_invoices

    def filter_validated_invoices(self, invoices):
        return self.filter_invoices(invoices)[0]

    def filter_failing_invoices(self, invoices):
        return self.filter_invoices(invoices)[1]

    def failing_invoices(self):
        return self._failing_invoices

    def format_message(self, exc_type, message):
        return "[{}] {}".format(exc_type.exc_code(), message)

    def impl_add_critical(self, invoice, exc_type, message):
        self._errors.setdefault(invoice.doc_filename, []).append(self.Entry(exc_type, message))
        self._failing_invoices[invoice.doc_filename] = invoice
        self.logger.critical(self.format_message(exc_type, message))
        raise exc_type(message)

    def impl_add_error(self, invoice, exc_type, message):
        self._errors.setdefault(invoice.doc_filename, []).append(self.Entry(exc_type, message))
        self._failing_invoices[invoice.doc_filename] = invoice
        self.logger.error(self.format_message(exc_type, message))

    def impl_add_warning(self, invoice, exc_type, message):
        self._warnings.setdefault(invoice.doc_filename, []).append(self.Entry(exc_type, message))
        self.logger.warning(self.format_message(exc_type, message))

    def impl_ignore(self, invoice, exc_type, message):
        pass

    def _exc_match(self, exc_type, suppression):
        return exc_type.__name__ in suppression or exc_type.exc_code() in suppression

    def add_error(self, invoice, exc_type, message):
        if self._exc_match(exc_type, self.error_suppression):
            self.logger.debug("fattura {}: errore {} ({}) soppresso".format(invoice.doc_filename, exc_type.__name__, message))
        else:
            self._function_error(invoice, exc_type, message)

    def add_warning(self, invoice, exc_type, message):
        if self._exc_match(exc_type, self.warning_suppression):
            self.logger.debug("fattura {}: warning {} ({}) soppresso".format(invoice.doc_filename, exc_type.__name__, message))
        else:
            self._function_warning(invoice, exc_type, message)

    def __bool__(self):
        return len(self._errors) == 0

    def num_errors(self):
        return sum(len(l) for l in self._errors.values())

    def num_warnings(self):
        return sum(len(l) for l in self._warnings.values())

    def errors(self):
        return self._errors

    def warnings(self):
        return self._warnings
