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

from . import notify_pyqt4
from . import notify_logger

if notify_pyqt4.available():
    notify = notify_pyqt4.notify
elif notify_logger.available():
    notify = notify_logger.notify
else:
    notify = None

def available(): # pragma: no cover
    return notify is not None
