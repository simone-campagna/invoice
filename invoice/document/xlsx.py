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
        super().__init__(logger=logger, page_options=page_options)

    def create_page_template(self, field_names, *, header=None, getter=None, convert=None, align=None, **options):
        options = self.page_template_options(options)
        return XlsxPageTemplate(document=self, field_names=field_names, header=header,
                                getter=getter, convert=convert, align=align, **options)

    def add_page(self, page_template, data, title=None):
        worksheet = self.workbook.add_worksheet(title)
        for r, row in enumerate(page_template.transform(data)):
            for c, col in enumerate(row):
                worksheet.write(r, c, col)

    def close(self):
        self.workbook.close()
