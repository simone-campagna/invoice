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
    'observe',
    'DocObserver',
]

# pragma: no cover

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

import time

from . import conf
from .daemon import Daemon

class InvoiceDocEventHandler(PatternMatchingEventHandler):
    def __init__(self, event_queue, logger=None, **options):
        self.logger = logger
        self.event_queue = event_queue
        super().__init__(**options)

    def cleanup(self):
        pass

    def on_any_event(self, event):
        if self.logger:
            self.logger.warning("got event {}".format(event))
        self.event_queue.append(event)

def observe(dirdata, function, logger=None, watch_delay=1, watch_notify_level=None):
    if watch_notify_level is None:
        watch_notify_level = conf.DEFAULT_WATCH_NOTIFY_LEVEL
    watch_notify_level_index = conf.WATCH_NOTIFY_LEVEL_INDEX[watch_notify_level]
    if watch_notify_level_index == conf.WATCH_NOTIFY_LEVEL_INDEX[conf.WATCH_NOTIFY_LEVEL_INFO]:
        initial_watch_notify_level = conf.WATCH_NOTIFY_LEVEL_WARNING
    else:
        initial_watch_notify_level = watch_notify_level
    observer = Observer()
    event_queue = []
    for dirname, filepatterns in dirdata.items():
        if logger:
            logger.info("watching dir {}, patterns {}...".format(dirname, filepatterns))
            event_handler = InvoiceDocEventHandler(logger=logger, event_queue=event_queue, patterns=filepatterns)
            observer.schedule(event_handler, dirname,
                              recursive=True)
    function(event_queue=event_queue, watch_notify_level=initial_watch_notify_level)
    observer.start()
    try:
        while True:
            if event_queue:
                function(event_queue=event_queue, watch_notify_level=watch_notify_level)
                del event_queue[:]
            time.sleep(watch_delay)
    except KeyboardInterrupt:
        observer.stop()
    event_handler.cleanup()
    observer.join()


class DocObserver(Daemon):
    def __init__(self, dirdata, function, logger=None, watch_delay=1, watch_notify_level=None):
        self.dirdata = dirdata
        self.function = function
        self.logger = logger
        self.watch_delay = watch_delay
        self.watch_notify_level = watch_notify_level
        super().__init__(lock_file=conf.WATCH_LOCK_FILE,
                         stdout=conf.WATCH_LOG_FILE,
                         stderr=conf.WATCH_LOG_FILE,
                         name='watch')

    def run(self):
        observe(dirdata=self.dirdata,
                function=self.function,
                logger=self.logger,
                watch_delay=self.watch_delay,
                watch_notify_level=self.watch_notify_level)
