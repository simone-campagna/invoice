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

class BasePageTemplate(metaclass=abc.ABCMeta):
    def __init__(self, document, field_names, *, header=None, getter=None, convert=None, align=None):
        self.document = document
        self.field_names = field_names
        if header is False:
            self.show_header = False
            self.header = None
        else:
            self.show_header = True
            if header is None:
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
        
    def transform(self, data):
        if self.show_header and data:
            yield self.header
        convert = self.convert
        for entry in data:
            yield tuple(convert.get(field_name, str)(self.getter(entry, field_name)) for field_name in self.field_names)


class BaseDocument(metaclass=abc.ABCMeta):
    def __init__(self, logger, page_options=None):
        self.logger = logger
        if page_options is None:
            page_options = {}
        self.page_options = page_options

    @abc.abstractmethod
    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_page(self, page_template, data, title=None):
        raise NotImplementedError()

    def close(self):
        pass
