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

import sys

__author__ = "Simone Campagna"
__all__ = [
    'Progressbar',
]


class Progressbar(object):
    def __init__(self, maxvalue, *, stream=sys.stderr, maxlen=80, render_frequency=0.1):
        self.maxvalue = maxvalue
        self.stream = stream
        self.render_frequency = render_frequency / 100.0
        self._value = 0.0
        self._fmt = "[{bar}] {fraction:6.1%}"
        non_bar_length = len(self._fmt.format(bar="", fraction=1.0))
        self._bar_length = max(10, maxlen - non_bar_length)
        self._current_line = ""
        self._next_fraction = 0.0

    @property
    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self.render()

    def add_value(self, value):
        self.set_value(self._value + value)

    def __iadd__(self, value):
        self.add_value(value)

    def tick(self):
        self.add_value(1)

    def clear(self):
        self.stream.write("\r" + (" " * len(self._current_line) + "\r"))

    def render(self):
        if self.maxvalue == 0:
            return
        fraction = self._value / self.maxvalue
        if fraction < self._next_fraction:
            return
        self._next_fraction = min(1.0, fraction + self.render_frequency)
        nblocks = int(round(self._bar_length * fraction, 0))
        block = "#" * nblocks
        non_block = " " * (self._bar_length - nblocks)
        bar = block + non_block
        line = self._fmt.format(bar=bar, fraction=fraction)
        if line != self._current_line:
            self.clear()
            self.stream.write(line + '\r')
            self._current_line = line
        
    def complete(self):
        self.stream.write("\n")
        
       
        
