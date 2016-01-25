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

from .base import BasePageTemplate, BaseDocument
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
    pass


class XlsxDocument(BaseDocument):
    def __init__(self, logger, filename, page_options=None):
        self.workbook = Workbook(filename)
        self._formats = {}
        super().__init__(logger=logger, page_options=page_options)

    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        options = self.page_template_options(options)
        return XlsxPageTemplate(document=self, field_names=field_names, header=header,
                                getter=getter, convert=convert, align=align, **options)

    def define_format(self, format_name, format_data):
        self._formats[format_name] = self.workbook.add_format(format_data)

    def _add_rows(self, worksheet, rows, *, row_offset=0, formats=None):
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
                worksheet.write(r, c, col, rc_format)
        return num_rows

    def add_page(self, page_template, data, *, title=None, formats=None, prologue=None, epilogue=None):
        worksheet = self.workbook.add_worksheet(title)
        row_offset = 0
        if prologue:
            row_offset += self._add_rows(worksheet=worksheet, rows=prologue, formats=formats, row_offset=row_offset)
        rows = page_template.transform(data)
        row_offset += self._add_rows(worksheet=worksheet, rows=rows, formats=formats, row_offset=row_offset)
        if epilogue:
            row_offset += self._add_rows(worksheet=worksheet, rows=epilogue, formats=formats, row_offset=row_offset)

    def close(self):
        self.workbook.close()
