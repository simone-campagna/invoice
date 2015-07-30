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
    'has_popup'
    'popup',
]

def has_popup(): # pragma: no cover
    return True

def popup(logger, kind, title, text, detailed_text=None): # pragma: no cover
    if kind == 'info':
        log_function = logger.info
    elif kind == 'warning':
        log_function = logger.warning
    elif kind == 'error':
        log_function = logger.error
    log_function("=== {} ===".format(title))
    for s in text, detailed_text:
        if s:
            for l in s.split('\n'):
                log_function("  # {}".format(l))
            log_function("  #")
