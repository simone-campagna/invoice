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
import sys

from .base import BasePageTemplate, BaseDocument


__author__ = "Simone Campagna"
__all__ = [
    'TextDocument',
    'TextPageTemplate',
    'TEXT_AVAILABLE',
    'CsvDocument',
    'CsvPageTemplate',
    'SCsvPageTemplate',
    'CSV_AVAILABLE',
]


TEXT_AVAILABLE = True
CSV_AVAILABLE = True


class BaseTCPageTemplate(BasePageTemplate):
    JUSTIFY = True
    FIELD_SEPARATOR = " "
    def __init__(self, document, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        super().__init__(document=document, field_names=field_names, header=header, getter=getter, convert=convert, align=align)
        justify = options.get("justify", None)
        if justify is None:
            justify = self.JUSTIFY
        self.justify = justify
        field_separator = options.get("field_separator", None)
        if field_separator is None:
            field_separator = self.FIELD_SEPARATOR
        self.field_separator = field_separator

    def getlines(self, data):
        rows = tuple(self.transform(data))
        if rows:
            if self.justify:
                lengths = [max(len(entry[c]) for entry in rows) for c, f in enumerate(self.field_names)]
            else:
                lengths = ['' for f in self.field_names]
            fmt = self.field_separator.join("{{row[{i}]:{align}{{lengths[{i}]}}s}}".format(i=i, align=self.align.get(f, '<')) for i, f in enumerate(self.field_names))
            for row in rows:
                yield fmt.format(row=row, lengths=lengths)

    def transform_value(self, value):
        if value is None:
            return ''
        else:
            return super().transform_value(value)


class TextPageTemplate(BaseTCPageTemplate):
    JUSTIFY = True
    FIELD_SEPARATOR = " "


class CsvPageTemplate(BaseTCPageTemplate):
    JUSTIFY = False
    FIELD_SEPARATOR = ","


class SCsvPageTemplate(CsvPageTemplate):
    JUSTIFY = False
    FIELD_SEPARATOR = ";"


class BaseTCDocument(BaseDocument):
    def __init__(self, logger, file=sys.stdout, page_options=None):
        self.file = file
        super().__init__(logger=logger, page_options=page_options)

    @abc.abstractmethod
    def _show_title(self, title):
        raise NotImplementedError()

    def define_format(self, format_name, format_data):
        pass

    def _add_xxxlogue(self, xxxlogue, pre, post):
        if xxxlogue:
            lines = []
            for row in xxxlogue:
                if not isinstance(row, str):
                    row = ' '.join(row)
                lines.append(row)
            if lines:
                #self.file.write(pre)
                self.file.write('\n'.join(lines) + '\n')
                #self.file.write(post)
        
    def _add_prologue(self, prologue):
        self._add_xxxlogue(prologue, pre="", post="\n")

    def _add_epilogue(self, epilogue):
        self._add_xxxlogue(epilogue, pre="\n", post="")

    def add_page(self, page_template, data, *, title=None, formats=None, prologue=None, epilogue=None):
        self._add_prologue(prologue)
        text = "\n".join(page_template.getlines(data))
        if text:
            text += "\n"
        self._show_title(title)
        self.file.write(text)
        self._add_epilogue(epilogue)

    @abc.abstractmethod
    def page_template_class(cls):
        raise NotImplementedError()

    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        options = self.page_template_options(options)
        return self.page_template_class()(document=self, field_names=field_names, header=header,
                                          getter=getter, convert=convert, align=align, **options)


class TextDocument(BaseTCDocument):
    def page_template_class(cls):
        return TextPageTemplate

    def _show_title(self, title):
        if title:
            self.file.write("=== {} ===\n".format(title))


class CsvDocument(BaseTCDocument):
    def page_template_class(cls):
        return CsvPageTemplate

    def _show_title(self, title):
        if title:
            self.file.write("# {}\n".format(title))


class SCsvDocument(CsvDocument):
    def page_template_class(cls):
        return SCsvPageTemplate
