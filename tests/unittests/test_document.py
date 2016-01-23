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

import collections
import io
import unittest

from invoice.document import document
from invoice import conf

__author__ = "Simone Campagna"
__all__ = [
    'TestDocument',
]


_Invoice = collections.namedtuple("_Invoice", ("name", "income", "tax_code"))

class TestDocument(unittest.TestCase):
    def setUp(self):
        self.invoices = [
            _Invoice(name="Peter Parker", income=400.0, tax_code="PRKPRT01A01B001C"),
            _Invoice(name="Peter Parker", income=450.0, tax_code="PRKPRT01A01B001C"),
            _Invoice(name="Clark Kent", income=423.122, tax_code="KNTCKR01A01B001C"),
        ]

    def _test_render(self, convert, align, header, output, mode=conf.DEFAULT_TABLE_MODE, options=None):
        sio = io.StringIO()
        if options is None:
            options = {}
        with document(mode=mode, file=sio) as doc:
            page_template = doc.create_page_template(
                field_names=_Invoice._fields,
                convert=convert,
                align=align,
                header=header,
                **options
            )
            doc.add_page(page_template, self.invoices)
            self.assertEqual(sio.getvalue(), output)

    def test_render_0(self):
        self.maxDiff = None
        self._test_render(
            convert=None,
            align=None,
            header=True,
            output="""\
name         income  tax_code        
Peter Parker 400.0   PRKPRT01A01B001C
Peter Parker 450.0   PRKPRT01A01B001C
Clark Kent   423.122 KNTCKR01A01B001C
""")

    def test_render_1(self):
        self._test_render(
            convert={'income': lambda value: '{:.2f}'.format(value)},
            align={'income': '>'},
            header=('nome e cognome', 'incasso', 'codice fiscale'),
            output="""\
nome e cognome incasso codice fiscale  
Peter Parker    400.00 PRKPRT01A01B001C
Peter Parker    450.00 PRKPRT01A01B001C
Clark Kent      423.12 KNTCKR01A01B001C
""")

    def test_render_2(self):
        self._test_render(
            options={'justify': False, 'field_separator': '|'},
            convert={'income': lambda value: '{:.2f}'.format(value)},
            align={'income': '>'},
            header=('nome e cognome', 'incasso', 'codice fiscale'),
            output="""\
nome e cognome|incasso|codice fiscale
Peter Parker|400.00|PRKPRT01A01B001C
Peter Parker|450.00|PRKPRT01A01B001C
Clark Kent|423.12|KNTCKR01A01B001C
""")

    def test_render_3(self):
        self._test_render(
            mode=conf.TABLE_MODE_CSV,
            convert={'income': lambda value: '{:.2f}'.format(value)},
            align={'income': '>'},
            header=('nome e cognome', 'incasso', 'codice fiscale'),
            output="""\
nome e cognome,incasso,codice fiscale
Peter Parker,400.00,PRKPRT01A01B001C
Peter Parker,450.00,PRKPRT01A01B001C
Clark Kent,423.12,KNTCKR01A01B001C
""")

