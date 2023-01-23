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

__all__ = ['filecopy',
           'backup',
           'tempcopy',
           'nocopy',
          ]


import os
import shutil

class filecopy(object):
    TMP_FILENAME_FORMAT = "{dirname}{sep}.{filename}.tmp.{index}"
    ERR_FILENAME_FORMAT = "{dirname}{sep}{filename}.err.{index}"
    def __init__(self, filename, tmp_filename_format=None, err_filename_format=None):
        if tmp_filename_format is None:
            tmp_filename_format = self.TMP_FILENAME_FORMAT
        self.tmp_filename_format = tmp_filename_format
        if err_filename_format is None:
            err_filename_format = self.ERR_FILENAME_FORMAT
        self.err_filename_format = err_filename_format
        self.filename = os.path.abspath(os.path.normpath(os.path.realpath(filename)))
        dirname, filename = os.path.split(self.filename)
        data = {}
        data['sep'] = os.path.sep
        data['dirname'] = dirname
        data['filename'] = filename
        index = 0
        prev_tmp_filename = None
        prev_err_filename = None
        while True:
            data['index'] = index
            tmp_filename = self.tmp_filename_format.format(**data)
            err_filename = self.err_filename_format.format(**data)
            is_valid = False
            if (os.path.exists(tmp_filename) and (tmp_filename != prev_tmp_filename)) or \
               (os.path.exists(err_filename) and (err_filename != prev_err_filename)):
                prev_tmp_filename = tmp_filename
                prev_err_filename = err_filename
                index += 1
                continue
            else:
                break
        self.tmp_filename = tmp_filename
        self.err_filename = err_filename

    def get_filename(self):
        return self.filename

    def on_enter(self):
        if os.path.exists(self.filename):
            shutil.copy(self.filename, self.tmp_filename)

    def on_exit_success(self):
        if os.path.exists(self.tmp_filename):
            os.remove(self.tmp_filename)

    def on_exit_failure(self, exc_type, exc_value, traceback):
        pass

    def __enter__(self):
        self.on_enter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.on_exit_success()
        else:
            self.on_exit_failure(exc_type, exc_value, traceback)

class backup(filecopy):
    TMP_FILENAME_FORMAT = "{dirname}{sep}.{filename}.bck.{index}"
    ERR_FILENAME_FORMAT = "{dirname}{sep}{filename}.err.{index}"

    def on_exit_failure(self, exc_type, exc_value, traceback):
        if os.path.exists(self.filename):
            os.rename(self.filename, self.err_filename)
        if os.path.exists(self.tmp_filename):
            os.rename(self.tmp_filename, self.filename)

class tempcopy(filecopy):
    def on_exit_failure(self, exc_type, exc_value, traceback):
        self.on_exit_success()

    def get_filename(self):
        return self.tmp_filename

class nocopy(filecopy):
    def __init__(self, *p_args, **n_args):
        super(nocopy, self).__init__(*p_args, **n_args)
        self.tmp_filename = self.filename
        self.err_filename = self.filename

    def on_enter(self):
        pass

    def on_exit_success(self):
        pass

    def on_exit_failure(self, exc_type, exc_value, traceback):
        pass

