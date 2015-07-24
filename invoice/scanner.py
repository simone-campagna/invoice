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
    'load_scanner',
]

import collections
import configparser
import os
import re
from .files import create_file_dir

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
            self._processed = True
            self._scan_lines.sort(key=lambda scan_line: scan_line.priority, reverse=True)

    def scan(self, document):
        return self.scan_lines(document.split('\n'))

    def scan_lines(self, lines):
        self.process()
        lines_dict = {}
        values_dict = {}
        lines_label_prio = {}
        for line in lines:
            for scan_line in self._scan_lines:
                prio = lines_label_prio.get(scan_line.tag, None)
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
                        lines_label_prio[scan_line.label] = scan_line.priority
        return lines_dict, values_dict

_DEFAULT_SCANNER_CONFIG = """\
[DEFAULT]
priority = 0
label =

[anno e numero]
regexpr = ^[Ff]attura\s+n.\s+(?P<year>\d+)/(?P<number>\d+)\s*$

[nome]
regexpr = ^\s*[Ss]pett\.\s*(?:[Ss]ig\.?|[Dd]ott\.?(?:\s*ssa)?)?\s*(?P<name>[\w\s'\.]+)\s*$

[codice fiscale]
regexpr = ^.*[^\w]?(?P<tax_code>[A-Z]{6,6}\d{2,2}[A-Z]\d{2,2}[A-Z]\d{3,3}[A-Z])\s*$

[codice fiscale sbagliato]
regexpr = ^.*[^\w](?P<tax_code>[A-Za-z0]{6,6}[\dO]{2,2}[A-Za-z0][\dO]{2,2}[A-Za-z0][\dO]{3,3}[A-Za-z0])\s*$
priority = -1
label = codice fiscale

[città e data]
regexpr = ^\s*(?P<city>[^,]+)(?:,|\s)\s*(?P<date>\d{1,2}/\d{1,2}/\d\d\d\d)\s*$

[importo e valuta]
regexpr = Totale\s+fattura\s+(?P<income>[\d,\.]*)\s+(?P<currency>\w+)\s*$

[prestazione]
regexpr = \s*(?:N\s*°\s*\d+|[Pp]restazione\s*:)\s*(?P<service>[^\d]*)(?:\s+[Pp][Ee][Rr]\s+)?\s*
"""

def load_scanner(scanner_config_filename):
    if not os.path.exists(scanner_config_filename):
        create_file_dir(scanner_config_filename)
        with open(scanner_config_filename, "w") as f_out:
            f_out.write(_DEFAULT_SCANNER_CONFIG)

    config = configparser.ConfigParser()
    config.read(scanner_config_filename)
    scanner = Scanner()
    for section_name in config.sections():
        section = config[section_name]
        tag = section_name
        label = section['label']
        regexpr = section['regexpr']
        priority = section['priority']
        if not label:
            label = tag
        scanner.add(ScanLine(
            tag=tag,
            label=label,
            regexpr=regexpr,
            priority=priority,
        ))
    return scanner

