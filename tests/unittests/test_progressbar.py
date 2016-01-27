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
    'TestProgressbar',
]

import io
import os
import unittest
import tempfile

from invoice.progressbar import Progressbar

class TestProgressbar(unittest.TestCase):
    def setUp(self):
        pass

    def test_tick(self):
        s = io.StringIO()
        ticks = 3
        maxlen = 30
        output = '\r\r[███████              ]  33.3%\r\r                              \r[██████████████       ]  66.7%\r\r                              \r[█████████████████████] 100.0%\r'
        pbar = Progressbar(ticks, stream=s, maxlen=maxlen)
        for i in range(ticks):
            pbar.tick()
        print(repr(s.getvalue()))
        assert s.getvalue() == output

    def test_add_value(self):
        s = io.StringIO()
        ticks = 10
        maxlen = 30
        output = '\r\r[██████▍              ]  30.0%\r\r                              \r[██████████▋          ]  50.0%\r\r                              \r[████████████████████ ]  95.0%\r\r                              \r[█████████████████████] 100.0%\r'
        pbar = Progressbar(ticks, stream=s, maxlen=maxlen)
        pbar.add_value(3)
        pbar.add_value(2)
        pbar.set_value(9.5)
        pbar.set_value(10.0)
        print(repr(s.getvalue()))
        assert s.getvalue() == output
