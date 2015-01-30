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
    'TestInvoiceProgram',
]

import os
import unittest

from invoice import conf

class TestConf(unittest.TestCase):
    def _update_env_dict(self, d0, d1):
        for key, val in d1.items():
            if val is None:
                if key in d0:
                    del d0[key]
            else:
                d0[key] = val

    def _test_env(self, rc_dir, db_file, updated_env_dict):
        saved_env_dict = {key: os.environ.get(key, None) for key in updated_env_dict}
        try:
            self._update_env_dict(os.environ, updated_env_dict)
            conf.setup()
            self.assertEqual(conf.RC_DIR, rc_dir)
            self.assertEqual(conf.DB_FILE, db_file)
        finally:
            self._update_env_dict(os.environ, saved_env_dict)
 

    def test_env_0(self):
        rc_dir = './alpha'
        db_file = 'xx.db'
        self._test_env(rc_dir=os.path.abspath(rc_dir),
                      db_file=os.path.abspath(os.path.join(rc_dir, db_file)),
                      updated_env_dict={conf.RC_DIR_VAR: rc_dir,
                                        conf.DB_FILE_VAR: db_file})

    def test_env_1(self):
        rc_dir = '/a/b/c/alpha'
        db_file = '/tmp/wru647d8/xx.db'
        self._test_env(rc_dir=rc_dir, db_file=db_file,
                      updated_env_dict={conf.RC_DIR_VAR: rc_dir,
                                        conf.DB_FILE_VAR: db_file})
    

