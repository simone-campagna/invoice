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

try: # pragma: no cover
    from PyQt5 import QtGui
    from PyQt5.QtCore import Qt
    HAS_PYQT = True
except ImportError:
    try: # pragma: no cover
        from PyQt4 import QtGui
        from PyQt4.QtCore import Qt
        HAS_PYQT = True
    except ImportError:
        HAS_PYQT = False

import sys

from . import text_formatter

_APP = None

def available(): # pragma: no cover
    return HAS_PYQT

if HAS_PYQT: # pragma: no cover
    def notify(logger, validation_result, scan_events, updated_invoice_collection, event_queue, spy_notify_level):
        notification_required, kind, title, text, detailed_text = text_formatter.formatter(
            validation_result=validation_result,
            scan_events=scan_events,
            updated_invoice_collection=updated_invoice_collection,
            event_queue=event_queue,
            mode=text_formatter.MODE_LONG,
            spy_notify_level=spy_notify_level,
        )
        if notification_required:
            if kind == 'info':
                qtfunction = QtGui.QMessageBox.information
                icon = QtGui.QMessageBox.Information
            elif kind == 'warning':
                qtfunction = QtGui.QMessageBox.warning
                icon = QtGui.QMessageBox.Warning
            elif kind == 'error':
                qtfunction = QtGui.QMessageBox.critical
                icon = QtGui.QMessageBox.Critical
            global _APP
            if _APP is None:
                _APP = QtGui.QApplication(sys.argv)
      
            mb = QtGui.QMessageBox(icon, title, text)
            mb.setTextFormat(Qt.LogText)
            mb.setSizeGripEnabled(True)
            size_policy = QtGui.QSizePolicy.Expanding
            mb.setSizePolicy(size_policy, size_policy)
            mb.setInformativeText(detailed_text)
            mb.setWindowModality(Qt.WindowModal)
            mb.exec_()
else:
    notify = None
