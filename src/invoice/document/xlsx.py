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

import contextlib
from .. import conf
from ..log import get_default_logger

from .base import BasePageTemplate, BaseDocument, Formula
from .formats import Formats

try:
    from xlsxwriter.workbook import Workbook
    XLSX_AVAILABLE = True
except ImportError as err: # pragma: no cover
    XLSX_AVAILABLE = False

__author__ = "Simone Campagna"
__all__ = [
    'XlsxPageTemplate',
    'XlsxDocument',
    'XLSX_AVAILABLE',
]


class XlsxPageTemplate(BasePageTemplate):
    def transform(self, data):
        if self.show_header and data:
            yield self.header
        convert = self.convert
        for entry in data:
            yield tuple(convert.get(field_name, lambda x: x)(self.getter(entry, field_name)) for field_name in self.field_names)



class XlsxDocument(BaseDocument):
    def __init__(self, logger, filename, page_options=None):
        self.workbook = Workbook(filename)
        self._formats = {}
        super().__init__(logger=logger, page_options=page_options)
        self._merge_format = self.workbook.add_format({
            #'bold':     True,
            'border':   10,
            #'align':    'center',
            'valign':   'vcenter',
            #'fg_color': '#D7E4BC',
        })

    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        options = self.page_template_options(options)
        return XlsxPageTemplate(document=self, field_names=field_names, header=header,
                                getter=getter, convert=convert, align=align, **options)

    def define_format(self, format_name, format_data):
        self._formats[format_name] = self.workbook.add_format(format_data)

    def _add_rows(self, worksheet, rows, *, row_offset=0, formats=None, formula_offset=0):
        num_rows = 0
        for ridx, row in enumerate(rows):
            r = row_offset + ridx
            num_rows += 1
            for c, col in enumerate(row):
                rc_format = None
                if formats:
                    format_name = formats.get_format(r, c)
                    if format_name:
                        rc_format = self._formats.get(format_name)
                if isinstance(col, Formula):
                    worksheet.write(r, c, col.get_formula(offset=formula_offset), rc_format, col.value)
                else:
                    worksheet.write(r, c, col, rc_format)
        return num_rows

    def _add_xxxlogue(self, worksheet, row_offset, xxxlogue, formats, pre, post):
        added_offset = 0
        if xxxlogue:
            rrfirst = row_offset
            row_offset += len(xxxlogue)
            text = '\n'.join(' '.join(row) for row in xxxlogue)
            num = 1
            if pre:
                if formats:
                    formats.apply_offset(row_offset, num)
                rrfirst += num
                row_offset += num
                added_offset += num
            worksheet.merge_range(rrfirst, 0, row_offset - 1, 100, text, self._merge_format)
            if post:
                if formats:
                    formats.apply_offset(row_offset, num)
                row_offset += num
                added_offset += num
        return row_offset, added_offset
        
    def _add_prologue(self, worksheet, row_offset, prologue, formats):
        return self._add_xxxlogue(worksheet, row_offset, prologue, formats, pre=False, post=True)

    def _add_epilogue(self, worksheet, row_offset, prologue, formats):
        return self._add_xxxlogue(worksheet, row_offset, prologue, formats, pre=True, post=False)

    def add_page(self, page_template, data, *, title=None, formats=None, prologue=None, epilogue=None):
        worksheet = self.workbook.add_worksheet(title)
        row_offset = 0
        #if prologue:
        #    #row_offset += self._add_rows(worksheet=worksheet, rows=prologue, formats=formats, row_offset=row_offset)
        #    #rrfirst = row_offset
        #    #row_offset + len(prologue)
        #    #worksheet.merge_range(rrfirst, row_offset, 0, 100, '\n'.join(" ".join(row) for row in prologue))
        row_offset, added_offset = self._add_prologue(worksheet, row_offset, prologue, formats)
        formula_offset = added_offset + 1  # row numbering starts with 1
        rows = tuple(page_template.transform(data))
        if rows:
            lengths = [max(len(str(entry[c])) for entry in rows) for c, f in enumerate(page_template.field_names)]
            for c, length in enumerate(lengths):
                l = 8.43 * length / 6
                worksheet.set_column(c, c, l)
        row_offset += self._add_rows(worksheet=worksheet, rows=rows, formats=formats, row_offset=row_offset, formula_offset=formula_offset)
        #if epilogue:
        #    #row_offset += self._add_rows(worksheet=worksheet, rows=epilogue, formats=formats, row_offset=row_offset)
        #    rrfirst = row_offset
        #    row_offset + len(epilogue)
        #    worksheet.merge_range(rrfirst, row_offset, 0, 100, '\n'.join(" ".join(row) for row in epilogue))
        row_offset = self._add_epilogue(worksheet, row_offset, epilogue, formats)

    def close(self):
        self.workbook.close()
