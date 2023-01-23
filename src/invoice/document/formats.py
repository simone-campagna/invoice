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


__author__ = "Simone Campagna"
__all__ = [
    'Formats',
]


class Formats(object):
    def __init__(self):
        self._formats = collections.OrderedDict()

    def add_format(self, format, *, row=None, col=None):
        if not row in self._formats:
            self._formats[row] = collections.OrderedDict()
        row_formats = self._formats[row]
        row_formats[col] = format

    def get_format(self, row, col):
        rc_format_name = None
        for rkey in None, row:
            if rkey in self._formats:
                row_formats = self._formats[rkey]
                for ckey in None, col:
                    if ckey in row_formats:
                        rc_format_name = row_formats[ckey]
        return rc_format_name

    def apply_offset(self, row, offset):
        swp = self._formats
        self._formats = collections.OrderedDict()
        for key, value in swp.items():
            if key is not None and key >= row:
                key += offset
            self._formats[key] = value
