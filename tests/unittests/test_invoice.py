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
    'TestInvoice',
]

import datetime
import unittest

from invoice.invoice import Invoice

class TestInvoice(unittest.TestCase):
    def setUp(self):
        pass

    # invoice
    def test_Invoice(self):
        invoice = Invoice(doc_filename='x.doc', year=2015, number=1, name='Peter B. Parker', tax_code='PRKPRT01A01B123C', 
            city='New York', date=datetime.date(2015, 1, 1), income=200.0, currency='euro')

