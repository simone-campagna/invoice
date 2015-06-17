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
    'Table'
]

from . import conf
from .log import get_default_logger

class Table(object):
    ITEM_GETTER = lambda row, field_name: row.get(field_name)
    ATTR_GETTER = lambda row, field_name: getattr(row, field_name)
    def __init__(self, field_names, mode=conf.TABLE_MODE_TEXT, justify=None, field_separator=None, convert=None, align=None, header=None, getter=None, logger=None):
        if mode == conf.TABLE_MODE_CSV:
            default_justify = False
            default_field_separator = ','
        else: # conf.TABLE_MODE_TEXT
            default_justify = True
            default_field_separator = ' '
        self.mode = mode
        if logger is None:
            logger = get_default_logger()
        self.logger = logger
        if justify is None:
            justify = default_justify
        if field_separator is None:
            field_separator = default_field_separator
        self.field_names = field_names
        self.justify = justify
        self.field_separator = field_separator
        if convert is None:
            convert = {}
        self.convert = convert
        if align is None:
            align = {}
        self.align = align
        if header is False:
            self.show_header = False
        else:
            self.show_header = True
            if header is None or header is True:
                header = field_names
            self.header = header
        if getter is None:
            getter = self.__class__.ATTR_GETTER
        self.getter = getter

    def transform(self, data):
        if self.show_header and data:
            yield self.header
        for entry in data:
            yield tuple(self.convert.get(field_name, str)(self.getter(entry, field_name)) for field_name in self.field_names)

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

    def render(self, data):
        return '\n'.join(self.getlines(data))

    def write(self, data, to):
        if isinstance(to, str):
            filename = to.format(mode=self.mode)
            if self.mode == conf.TABLE_MODE_XLSX:
                self.write_xlsx(data, filename)
            else:
                with open(filename, "w") as f_out:
                    for line in self.getlines(data):
                        f_out.write(line + '\n')
        else:
            printer = to
            if self.mode == conf.TABLE_MODE_XLSX:
                self.logger.warning("non è possibile produrre su terminale una tabella in modalità {}; utilizzare l'opzione --output/-o".format(self.mode))
            else:
                for line in self.getlines(data):
                    printer(line)

    def write_xlsx(self, data, filename):
        try:
            from xlsxwriter.workbook import Workbook
        except ImportError as err: # pragma: no cover
            raise ImportError("modulo 'xlsxwriter' non trovato - prova ad installare python3-xlsxwriter")
        workbook = Workbook(filename.format(mode=self.mode))
        worksheet = workbook.add_worksheet()
        for r, row in enumerate(self.transform(data)):
            for c, col in enumerate(row):
                worksheet.write(r, c, col)

