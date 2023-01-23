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
    'load_info',
]

import configparser
import os

from . import conf
from .files import create_file_dir

_DEFAULT_INFO_CONFIG = """\
[general]
summary_prologue =
summary_epilogue =

"""

def load_info(info_config_filename=None):
    if info_config_filename is None:
        info_config_filename = conf.INFO_CONFIG_FILE
    if not os.path.exists(info_config_filename):
        create_file_dir(info_config_filename)
        with open(info_config_filename, "w") as f_out:
            f_out.write(_DEFAULT_INFO_CONFIG)

    config = configparser.ConfigParser(interpolation=None)
    config.read(info_config_filename)
    info = {}
    for section_name in ('general',):
        if section_name in config:
            dct = dict(config[section_name])
        else:
            dct = {}
        info[section_name] = dct
    return info

