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
import sys

scripts = [
	'bin/invoice',
]

try:
    dirname = os.path.dirname(os.path.abspath(sys.argv[0]))
    py_dirname = dirname
    sys.path.insert(0, py_dirname)

    from invoice import conf
    version = conf.VERSION
finally:
    del sys.path[0]

setup(
    name = "invoice",
    version = version,
    requires = [],
    description = "Tool to read and process invoices",
    author = "Simone Campagna",
    author_email = "simone.campagna11@gmail.com",
    url="https://github.com/simone-campagna/invoice",
    download_url = 'https://github.com/simone-campagna/invoice/archive/{}.tar.gz'.format(version),
    packages = [
        'invoice',
        'invoice.database',
    ],
    scripts = scripts,
    package_data = {},
)

