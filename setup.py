#
# Copyright 2013 Simone Campagna
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

from distutils.core import setup
import os
import glob
import sys

def main():
    scripts = [
	'bin/invoice',
    ]

    DIRNAME = os.path.abspath(os.path.dirname(__file__))
    if DIRNAME:
        os.chdir(DIRNAME)
    try:
        py_dirname = DIRNAME
        sys.path.insert(0, py_dirname)

        from invoice.conf import VERSION
    finally:
        del sys.path[0]

    # search requirement files
    data_files = []
    for data_dirname, patterns in [('requirements', ('*.txt', )),
                                   ('docs/sphinx/source', ('conf.py', '*.rst')),
                                   ('docs/sphinx/source/img', ('*.jpg',)),
                                  ]:
        files = []
        for pattern in patterns:
            for fpath in glob.glob(os.path.join(DIRNAME, data_dirname, pattern)):
                files.append(os.path.relpath(fpath, DIRNAME))
        data_files.append((data_dirname, files))
    
    setup(
        name = "invoice",
        version = VERSION,
        requires = [],
        description = "Tool to read and process invoices",
        author = "Simone Campagna",
        author_email = "simone.campagna11@gmail.com",
        url="https://github.com/simone-campagna/invoice",
        download_url = 'https://github.com/simone-campagna/invoice/archive/{}.tar.gz'.format(VERSION),
        packages = [
            'invoice',
            'invoice.database',
            'invoice.database.upgrade',
            'invoice.document',
            'invoice.ee',
            'invoice.spy',
        ],
        package_data = {'invoice.spy': ['icons/*.jpg']},
        data_files=data_files,
        scripts = scripts,
    )

if __name__ == "__main__":
    main()
