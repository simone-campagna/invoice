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
    'spy_function'
]

from .. import conf
from . import popup_pyqt4
from . import popup_logger

def spy_function(program, event_queue, spy_notify_level=None): # pragma: no cover
    result, scan_events, updated_invoice_collection = program.impl_scan()
    program.logger.info("result: {}".format(result))
    lines = []
    detailed_lines = []
    popup_type = 'info'
    program.db.reset_config_cache()
    spy_notify_level = program.db.get_config_option('spy_notify_level', spy_notify_level)
    spy_notify_level_index = conf.SPY_NOTIFY_LEVEL_INDEX[spy_notify_level]

    max_warnings = 3
    max_errors = 3

    popups = []
    for popup_module in popup_logger, popup_pyqt4:
        if popup_module.has_popup():
            popups.append(popup_module.popup)

    def welines(max, items):
        count = 0
        ls = []
        for doc_filename, entries in items:
            for entry in entries:
                if count < max:
                    ls.append("+ {}".format(entry.message))
                count += 1
        return ls
        
    if result.num_errors() + result.num_warnings() == 0:
        if updated_invoice_collection and spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_INFO]:
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
        if result.num_warnings() > 0 and spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_WARNING]:
            popup_type = 'warning'
            wes.append("#{} warning".format(result.num_warnings()))
            detailed_lines.append("=== warning:")
            detailed_lines.extend(welines(max_warnings, result.warnings().items()))
        if result.num_errors() > 0 and spy_notify_level_index <= conf.SPY_NOTIFY_LEVEL_INDEX[conf.SPY_NOTIFY_LEVEL_ERROR]:
            wes.append("#{} errori".format(result.num_errors()))
            detailed_lines.append("=== errori:")
            detailed_lines.extend(welines(max_errors, result.errors().items()))
            popup_type = 'error'
        if wes:
            lines.append("Trovati {}".format(', '.join(wes)))
    if lines or detailed_lines:
        text = '\n'.join(lines)
        if detailed_lines:
            detailed_text = '\n'.join(detailed_lines)
        else:
            detailed_text = None
        for popup in popups:
            popup(logger=program.logger, kind=popup_type, title="Invoice Spy", text=text, detailed_text=detailed_text)
