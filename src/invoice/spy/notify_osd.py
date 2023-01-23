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

import os

try: # pragma: no cover
    import notify2
    HAS_NOTIFY2 = True
except ImportError:
    HAS_NOTIFY2 = False

from . import text_formatter


_NOTIFICATION = None

def available(): # pragma: no cover
    return HAS_NOTIFY2

_PACKAGE_DIR = os.path.dirname(__file__)
_ICONS = {
    'info': os.path.join(_PACKAGE_DIR, 'icons', 'logo_info.jpg'),
    'warning': os.path.join(_PACKAGE_DIR, 'icons', 'logo_warning.jpg'),
    'error': os.path.join(_PACKAGE_DIR, 'icons', 'logo_error.jpg'),
}

if HAS_NOTIFY2: # pragma: no cover
    def notify(logger, validation_result, scan_events, updated_invoice_collection, event_queue, spy_notify_level):
        notification_required, kind, title, text, detailed_text = text_formatter.formatter(
            validation_result=validation_result,
            scan_events=scan_events,
            updated_invoice_collection=updated_invoice_collection,
            event_queue=event_queue,
            mode=text_formatter.MODE_SHORT,
            spy_notify_level=spy_notify_level,
        )
        if notification_required:
            global _NOTIFICATION
            summary = title + ' [{}]'.format(kind.upper())
            message = text
            if detailed_text:
                message += '\n\n' + detailed_text
            icon = _ICONS[kind]
            if _NOTIFICATION is None:
                notify2.init("Invoice spy [{}]".format(kind.upper()))
                _NOTIFICATION = notify2.Notification(summary=summary, message=message, icon=icon)
            notification = _NOTIFICATION
            urgency_d = {
                'info': notify2.URGENCY_LOW,
                'warning': notify2.URGENCY_NORMAL,
                'error': notify2.URGENCY_CRITICAL,
            }
            notification.update(summary=summary, message=message, icon=icon)
            notification.set_urgency(urgency_d[kind])
            notification.show()
else:
    notify = None
