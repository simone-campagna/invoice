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
    'popup',
    'popup_info',
    'popup_warning',
    'popup_error',
]


from PyQt4 import QtGui
import sys


def popup(kind, title, text, x=None, y=None):
    if kind == 'info':
        qtfunction = QtGui.QMessageBox.information
    elif kind == 'warning':
        qtfunction = QtGui.QMessageBox.warning
    elif kind == 'error':
        qtfunction = QtGui.QMessageBox.critical
    app = QtGui.QApplication(sys.argv)
    qtfunction(None, title, text)

def popup_info(title, text):
    return popup('info', title, text)

def popup_warning(title, text):
    return popup('warning', title, text)

def popup_error(title, text):
    return popup('error', title, text)
