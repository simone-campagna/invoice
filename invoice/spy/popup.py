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
    'popup_info',
    'popup_warning',
    'popup_error',
]

try: # pragma: no cover
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt
    HAS_PYQT4 = True
except ImportError:
    HAS_PYQT4 = False
import sys

_APP = None

def has_popup(): # pragma: no cover
    return HAS_PYQT4

if HAS_PYQT4: # pragma: no cover
    def popup(kind, title, text, detailed_text=None):
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
    
    def popup_info(title, text, detailed_text=None):
        return popup('info', title, text, detailed_text=detailed_text)
    
    def popup_warning(title, text, detailed_text=None):
        return popup('warning', title, text, detailed_text=detailed_text)
    
    def popup_error(title, text, detailed_text=None):
        return popup('error', title, text, detailed_text=detailed_text)
else:
    popup = None
    popup_info = None
    popup_warning = None
    popup_error = None
