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
    'Upgrader',
    'UpgraderMeta',
    'MajorMinorUpgrader',
    'PatchUpgrader',
    'Upgrader_v2_0_x__v2_1_0',
    'Upgrader_v2_1_x__v2_2_0',
    'Upgrader_v2_2_x__v2_3_0',
    'Upgrader_v2_3_x__v2_4_0',
]

from .upgrader import UpgraderMeta, Upgrader, MajorMinorUpgrader
from .patch_upgrader import PatchUpgrader
from .upgrader_v2_0_x__v2_1_0 import Upgrader_v2_0_x__v2_1_0
from .upgrader_v2_1_x__v2_2_0 import Upgrader_v2_1_x__v2_2_0
from .upgrader_v2_2_x__v2_3_0 import Upgrader_v2_2_x__v2_3_0
from .upgrader_v2_3_x__v2_4_0 import Upgrader_v2_3_x__v2_4_0
