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
import sys

from .. import conf
from ..error import InvoiceArgumentError
from ..log import get_default_logger


__author__ = "Simone Campagna"
__all__ = [
    'document'
]

from .text_csv import TextDocument, CsvDocument
from .xlsx import XlsxDocument, XLSX_AVAILABLE


@contextlib.contextmanager
def document(mode=conf.TABLE_MODE_TEXT, file=None, *, logger=None):
    if logger is None:
        logger = get_default_logger()
    has_filename = False
    if file is None:
        file = sys.stdout
    if isinstance(file, str):
        has_filename = True
    if has_filename:
        file = file.format(mode=mode)
    must_close = False
    if mode == conf.TABLE_MODE_XLSX:
        if not has_filename:
            raise InvoiceArgumentError("non è possibile produrre una tabella in formato {} su terminale; utilizzare --output".format(mode))
        if not XLSX_AVAILABLE:
            raise ImportError("modulo 'xlsxwriter' non trovato - prova ad installare python3-xlsxwriter")
        doc = XlsxDocument(logger=logger, filename=file)
    else:
        if has_filename:
            file_handle = open(file, "w")
            must_close = True
        else:
            file_handle = file
            must_close = False
        if mode == conf.TABLE_MODE_TEXT:
            document_class = TextDocument
        elif mode == conf.TABLE_MODE_CSV:
            document_class = CsvDocument
        doc = document_class(logger=logger, file=file_handle)
    yield doc
    if must_close:
        file_handle.close()
    doc.close()

