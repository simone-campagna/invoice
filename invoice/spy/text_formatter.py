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
    'formatter',
    'MODE_LONG',
    'MODE_SHORT',
]

import os

from .. import conf

MODE_LONG = 'long'
MODE_SHORT = 'short'


def we_long(max, items):
    count = 0
    ls = []
    for doc_filename, entries in items:
        for entry in entries:
            if count < max:
                ls.append("+ {}".format(entry.message))
            count += 1
    return ls

def we_short(max, items):
    count = 0
    ls = []
    maxlen = 30
    for doc_filename, entries in items:
        if len(doc_filename) > maxlen:
            m = '...' + doc_filename[-(maxlen - 3):]
        else:
            m = doc_filename
        ls.append("+ {}".format(m))
        count += 1
    return ls

_WE_FUNCTIONS = {
    MODE_LONG: we_long,
    MODE_SHORT: we_short,
}
def formatter(validation_result, scan_events, updated_invoice_collection, event_queue, mode, spy_notify_level): # pragma: no cover
    max_warnings = 3
    max_errors = 3

    we_function = _WE_FUNCTIONS[mode]
    spy_notify_level_index = conf.SPY_NOTIFY_LEVEL_INDEX[spy_notify_level]
    kind = 'info'
    lines = []
    detailed_lines = []

    if validation_result.num_errors() + validation_result.num_warnings() == 0:
        if spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_INFO]:
            rl = []
            trd = {
                'added': 'aggiunte',
                'modified': 'modificate',
                'removed': 'rimosse',
            }
            for scan_event_type in 'added', 'modified', 'removed':
                num_invoices = scan_events[scan_event_type]
                if num_invoices > 0:
                    rl.append("{}: {}".format(trd[scan_event_type], num_invoices))
            if rl:
                lines.append("Scansione eseguita con successo!")
                lines.append("Fatture {}".format(', '.join(rl)))
    else:
        wes = []
        if validation_result.num_warnings() > 0 and spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_WARNING]:
            kind = 'warning'
            wes.append("#{} warning".format(validation_result.num_warnings()))
            if mode == MODE_LONG:
                detailed_lines.append("=== warning:")
            detailed_lines.extend(we_function(max_warnings, validation_result.warnings().items()))
        if validation_result.num_errors() > 0 and spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_ERROR]:
            wes.append("#{} errori".format(validation_result.num_errors()))
            if mode == MODE_LONG:
                detailed_lines.append("=== errori:")
            detailed_lines.extend(we_function(max_errors, validation_result.errors().items()))
            kind = 'error'
        if wes:
            lines.append("Scansione eseguita con {}".format(', '.join(wes)))
    text = None
    detailed_text = None
    notification_required = False
    if lines or detailed_lines:
        notification_required = True
        text = '\n'.join(lines)
        if detailed_lines:
            detailed_text = '\n'.join(detailed_lines)
    title = "invoice spy"
    return notification_required, kind, title, text, detailed_text
