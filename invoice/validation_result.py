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
import fnmatch

from .error import InvoiceValidationError

class ValidationResult(object):
    WARNING_ACTION_LOG = 'log'
    WARNING_ACTION_ERROR = 'error'
    WARNING_ACTION_IGNORE = 'ignore'
    WARNING_ACTION_RAISE = 'raise'
    WARNING_ACTIONS = (WARNING_ACTION_LOG, WARNING_ACTION_ERROR, WARNING_ACTION_IGNORE, WARNING_ACTION_RAISE)
    DEFAULT_WARNING_ACTION = WARNING_ACTION_LOG
    DEFAULT_WARNING_MODE = ("{}:*".format(DEFAULT_WARNING_ACTION), )

    ERROR_ACTION_LOG = 'log'
    ERROR_ACTION_IGNORE = 'ignore'
    ERROR_ACTION_RAISE = 'raise'
    ERROR_ACTIONS = (ERROR_ACTION_LOG, ERROR_ACTION_IGNORE, ERROR_ACTION_RAISE)
    DEFAULT_ERROR_ACTION = ERROR_ACTION_LOG
    DEFAULT_ERROR_MODE = ("{}:*".format(DEFAULT_ERROR_ACTION), )

    Entry = collections.namedtuple('Entry', ('exc_type', 'message'))

    def __init__(self, logger, warning_mode=DEFAULT_WARNING_MODE, error_mode=DEFAULT_ERROR_MODE):
        self._failing_invoices = dict()
        self.logger = logger
        self._errors = collections.OrderedDict()
        self._warnings = collections.OrderedDict()

        if error_mode is None:
            error_mode = self.DEFAULT_ERROR_MODE
        self.error_mode = error_mode

        if warning_mode is None:
            warning_mode = self.DEFAULT_WARNING_MODE
        self.warning_mode = warning_mode

        self.error_function = {
            self.ERROR_ACTION_LOG: self.impl_add_error,
            self.ERROR_ACTION_RAISE: self.impl_add_critical,
            self.ERROR_ACTION_IGNORE: self.impl_ignore,
        }
        self.warning_function = {
            self.WARNING_ACTION_LOG: self.impl_add_warning,
            self.WARNING_ACTION_ERROR: self.impl_add_error,
            self.WARNING_ACTION_RAISE: self.impl_add_critical,
            self.WARNING_ACTION_IGNORE: self.impl_ignore,
        }

        self.error_action = self._make_error_action(mode=error_mode)
        self.warning_action = self._make_warning_action(mode=warning_mode)


    @classmethod
    def _type_mode(cls, mode_item, *, mode_type, actions):
        ilist = [itoken.strip() for itoken in mode_item.split(':', 1)]
        action = ilist[0]
        if len(ilist) > 1:
            pattern = ilist[1]
        else:
            pattern = '*'
        if action not in actions:
            raise ValueError("{mt} {m!r}: azione {a!r} non valida (i valori leciti sono {al})".format(
                mt=mode_type,
                m=item,
                a=action,
                al='|'.join(actions),
            ))
        return action, pattern

    @classmethod
    def type_warning_mode(cls, mode_item):
        return cls._type_mode(mode_item=mode_item, mode_type='warning_mode', actions=cls.WARNING_ACTIONS)
        
    @classmethod
    def type_error_mode(cls, mode_item):
        return cls._type_mode(mode_item=mode_item, mode_type='error_mode', actions=cls.ERROR_ACTIONS)
        
    @classmethod
    def check_warning_mode(cls, mode_item):
        return ':'.join(cls.type_warning_mode(mode_item))

    @classmethod
    def check_error_mode(cls, mode_item):
        return ':'.join(cls.type_error_mode(mode_item))

    @classmethod
    def _make_action(cls, *, default_action, type_function, mode): 
        d = collections.defaultdict(lambda : default_action)
        exc_codes = [exc.exc_code() for exc in InvoiceValidationError.subclasses()]
        for mode_item in mode:
            action, pattern = type_function(mode_item)
            for exc_code in fnmatch.filter(exc_codes, pattern):
                d[exc_code] = action
        return d

    @classmethod
    def _make_warning_action(cls, mode):
        return cls._make_action(default_action=cls.DEFAULT_WARNING_ACTION, type_function=cls.type_warning_mode, mode=mode)

    @classmethod
    def _make_error_action(cls, mode):
        return cls._make_action(default_action=cls.DEFAULT_ERROR_ACTION, type_function=cls.type_error_mode, mode=mode)

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

    def add_error(self, invoice, exc_type, message):
        exc_code = exc_type.exc_code()
        action = self.error_action[exc_code]
        function = self.error_function[action]
        function(invoice, exc_type, message)

    def add_warning(self, invoice, exc_type, message):
        exc_code = exc_type.exc_code()
        action = self.warning_action[exc_code]
        function = self.warning_function[action]
        function(invoice, exc_type, message)

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
