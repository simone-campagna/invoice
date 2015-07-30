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
    'available'
    'notify',
]

from . import text_formatter


def available(): # pragma: no cover
    return True

def notify(logger, validation_result, scan_events, updated_invoice_collection, event_queue, spy_notify_level):  # pragma: no cover
    notification_required, kind, title, text, detailed_text = text_formatter.formatter(
        validation_result=validation_result,
        scan_events=scan_events,
        updated_invoice_collection=updated_invoice_collection,
        event_queue=event_queue,
        mode=text_formatter.MODE_LONG,
        spy_notify_level=spy_notify_level
    )
    if notification_required:
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
