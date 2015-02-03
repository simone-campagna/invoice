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
    'Table'
]

class Table(object):
    ITEM_GETTER = lambda row, field_name: row.get(field_name)
    ATTR_GETTER = lambda row, field_name: getattr(row, field_name)
    def __init__(self, field_names, convert=None, align=None, header=None, getter=None):
        self.field_names = field_names
        if convert is None:
            convert = {}
        self.convert = convert
        if align is None:
            align = {}
        self.align = align
        if header is False:
            self.show_header = False
        else:
            self.show_header = True
            if header is None:
                header = field_names
            self.header = header
        if getter is None:
            getter = self.__class__.ATTR_GETTER
        self.getter = getter

    def getlines(self, data):
        rows = []
        if self.show_header:
            rows.append(self.header)
        for entry in data:
            rows.append(tuple(self.convert.get(field_name, str)(self.getter(entry, field_name)) for field_name in self.field_names))
        if data:
            lengths = [max(len(entry[c]) for entry in rows) for c, f in enumerate(self.field_names)]
            fmt = " ".join("{{row[{i}]:{align}{{lengths[{i}]}}s}}".format(i=i, align=self.align.get(f, '<')) for i, f in enumerate(self.field_names))
            for row in rows:
                yield fmt.format(row=row, lengths=lengths)

    def render(self, data):
        return '\n'.join(self.getlines(data))
