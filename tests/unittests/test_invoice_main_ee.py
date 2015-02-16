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
    'Test_invoice_main',
]

import datetime
import unittest

from invoice.log import get_null_logger
from invoice.invoice_main import invoice_main
from invoice.string_printer import StringPrinter
from invoice.ee import snow

class Test_invoice_main(unittest.TestCase):
    def setUp(self):
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_ee_snow_flakes(self):
        p = StringPrinter()

        snow.set_animation(delay=0.01, duration=0.1)
        snow.set_printer(p)

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "snow"]
        )

    def test_invoice_main_ee_snow_money(self):
        p = StringPrinter()

        snow.set_animation(delay=0.01, duration=0.1)
        snow.set_printer(p)

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "money"]
        )
