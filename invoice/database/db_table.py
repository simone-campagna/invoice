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
    'DbTable',
]

import collections

class DbTable(object):
    def __init__(self, fields, dict_type=collections.OrderedDict, singleton=False):
        self.dict_type = dict_type
        self.fields = collections.OrderedDict(fields)
        if hasattr(self.dict_type, '_fields'):
             self.field_names = self.dict_type._fields
        else:
             self.field_names = tuple(self.fields.keys())
        self.singleton = singleton

