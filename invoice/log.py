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
    'get_logging_level',
    'create_logger',
    'set_verbose_level',
    'get_default_logger',
]

import logging

def get_logging_level(verbose_level):
    if verbose_level == 0:
        return logging.WARNING
    elif verbose_level == 1:
        return logging.INFO
    elif verbose_level >= 2:
        return logging.DEBUG

def create_logger(name, level=logging.WARNING, formatter=None):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    if formatter is None:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

def set_verbose_level(logger, verbose_level):
    level = get_logging_level(verbose_level)
    for handler in logger.handlers:
        handler.setLevel(level)
    logger.setLevel(level)

_DEFAULT_LOGGER = None

def get_default_logger():
    global _DEFAULT_LOGGER
    if _DEFAULT_LOGGER is None:
        _DEFAULT_LOGGER = create_logger('invoice')
    return _DEFAULT_LOGGER
