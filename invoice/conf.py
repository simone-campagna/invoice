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
    'VERSION_MAJOR',
    'VERSION_MINOR',
    'VERSION_PATCH',
    'VERSION',
    'RC_DIR_VAR',
    'DB_FILENAME_VAR',
    'RC_DIR',
    'DB_FILENAME',
]

import os

VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0

VERSION = '{}.{}.{}'.format(VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

RC_DIR_VAR = os.path.join('~', '.invoice')
DB_FILENAME_VAR = os.path.join(RC_DIR_VAR, 'invoices.db')
RC_DIR = os.path.expanduser(RC_DIR_VAR)
DB_FILENAME = os.path.expanduser(DB_FILENAME_VAR)
