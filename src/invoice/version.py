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
    'Version',
]

import collections

from . import conf

_VersionNamedTuple = collections.namedtuple('Version', ('major', 'minor', 'patch'))

class Version(_VersionNamedTuple):
    def __eq__(self, v):
        return all((x == y) for x, y in zip(self, v))

    def __ne__(self, v):
        return any((x != y) for x, y in zip(self, v))

    def _compare(self, other, function, equal=False):
        is_equal = True
        for s, o in zip(self, other):
            if function(s, o):
                return True
            elif s != o:
                is_equal = False
        return equal and is_equal

    def __lt__(self, other):
        return self._compare(other, function=lambda x, y: x < y, equal=False)

    def __le__(self, other):
        return self._compare(other, function=lambda x, y: x < y, equal=True)

    def __gt__(self, other):
        return self._compare(other, function=lambda x, y: x > y, equal=False)

    def __ge__(self, other):
        return self._compare(other, function=lambda x, y: x > y, equal=True)

    def __add__(self, other):
        return self.__class__(*(vs + vo for vs, vo in zip(self, other)))

    def __sub__(self, other):
        return self.__class__(*(vs - vo for vs, vo in zip(self, other)))

    def __str__(self):
        return ".".join(str(e) for e in self)

VERSION = Version(
    major=conf.VERSION_MAJOR,
    minor= conf.VERSION_MINOR,
    patch= conf.VERSION_PATCH)
