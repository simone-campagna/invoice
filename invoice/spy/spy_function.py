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

from . import notify_osd
from . import notify_logger


def spy_function(program, event_queue, spy_notify_level=None): # pragma: no cover
    validation_result, scan_events, updated_invoice_collection = program.impl_scan()
    program.logger.info("validation_result: {}".format(validation_result))
    program.db.reset_config_cache()
    spy_notify_level = program.db.get_config_option('spy_notify_level', spy_notify_level)

    notify_l = []
    for notify in notify_osd, notify_logger:
        if notify.available():
            notify_l.append(notify_osd)

    for notify in notify_l:
        notify.notify(logger=program.logger,
                      validation_result=validation_result,
                      scan_events=scan_events,
                      updated_invoice_collection=updated_invoice_collection,
                      event_queue=event_queue,
                      spy_notify_level=spy_notify_level)
