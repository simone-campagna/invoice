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
    'Scanner',
]

import collections
import re

class ScanLine(object):
    def __init__(self, tag, regexpr, label=None, priority=0):
        self.tag = tag
        if label is None:
            label = self.tag
        self.label = label
        self.priority = priority
        self.regexpr = regexpr
        self._cre = re.compile(regexpr)

    def scan(self, line):
        m = self._cre.match(line)
        if m is None:
            return None
        else:
            return dict(m.groupdict())


class Scanner(object):
    def __init__(self, init=None):
        self._scan_lines = []
        self._processed = False
        if init:
            for scan_line in init:
                self.add(scan_line)

    def add(self, scan_line):
        self._processed = False
        self._scan_lines.append(scan_line)

    def process(self):
        if not self._processed:
            self._processed = False
            self._scan_lines.sort(key=lambda scan_line: scan_line.priority, reverse=True)

    def scan(self, document):
        return self.scan_lines(document.split('\n'))

    def scan_lines(self, lines):
        self.process()
        lines_dict = {}
        values_dict = {}
        lines_tag_prio = {}
        for line in lines:
            for scan_line in self._scan_lines:
                prio = lines_tag_prio.get(scan_line.tag, None)
                if prio is None or prio < scan_line.priority:
                    reset = True
                    scan = True
                elif prio == scan_line.priority:
                    reset = False
                    scan = True
                else:
                    reset = False
                    scan = False
                if scan:
                    scan_line_dict = scan_line.scan(line)
                    if scan_line_dict is not None:
                        if reset:
                            lines_dict[scan_line.label] = [line]
                        else:
                            lines_dict.setdefault(scan_line.label, []).append(line)
                        values_dict.update(scan_line_dict)
                        lines_tag_prio[scan_line.tag] = scan_line.priority
        return lines_dict, values_dict
