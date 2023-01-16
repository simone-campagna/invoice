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

import abc


__author__ = "Simone Campagna"
__all__ = [
    'item_getter',
    'attr_getter',
    'BaseDocument',
    'BasePageTemplate',
]


def item_getter(row, field_name):
    return row.get(field_name)

def attr_getter(row, field_name):
    return getattr(row, field_name)

# Page template

class Formula(object):
    def __init__(self, formula, col, row_begin, row_end, value):
        self._formula = formula
        self.col = col
        self.row_begin = row_begin
        self.row_end = row_end
        self._value = value

    @classmethod
    def get_letter(cls, col):
        return chr(ord('A') + col)

    @property
    def value(self):
        return self._value

    @property
    def formula(self):
        return self.get_formula()

    def get_formula(self, offset=0):
        return "={f}({l}{rb}:{l}{re})".format(
            f=self._formula,
            l=self.get_letter(self.col),
            rb=self.row_begin + offset,
            re=self.row_end + offset,
        )

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.formula, self.value)


class BasePageTemplate(metaclass=abc.ABCMeta):
    def __init__(self, document, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        self.document = document
        self.field_names = field_names
        if header is False:
            self.show_header = False
            self.header = None
        else:
            self.show_header = True
            if header is None or header is True:
                self.header = field_names
            else:
                self.header = header
        if getter is None:
            getter = attr_getter
        self.getter = getter
        if convert is None:
            convert = {}
        self.convert = convert
        if align is None:
            align = {}
        self.align = align
        
    def transform_value(self, value):
        return value

    def transform(self, data):
        if self.show_header and data:
            yield self.header
        convert = self.convert
        for entry in data:
            yield tuple(convert.get(field_name, str)(self.transform_value(self.getter(entry, field_name))) for field_name in self.field_names)


class BaseDocument(metaclass=abc.ABCMeta):
    def __init__(self, logger, page_options=None):
        self.logger = logger
        if page_options is None:
            page_options = {}
        self.page_options = page_options

    @abc.abstractmethod
    def define_format(self, format_name, format_data):
        raise NotImplementedError()

    @abc.abstractmethod
    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        raise NotImplementedError()

    def page_template_options(self, options):
        opts = self.page_options.copy()
        opts.update(options)
        return opts

    @abc.abstractmethod
    def add_page(self, page_template, data, *, title=None, formats=None, prologue=None, epilogue=None):
        raise NotImplementedError()

    def close(self):
        pass
