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

from setuptools import setup, find_packages

VERSION = '4.0.0'  ### bumpversion!

def main():
    setup(
        name="invoice",
        version=VERSION,
        requires=[],
        install_requires=['openpyxl', 'XlsxWriter'],
        description="Tool to read and process invoices",
        author="Simone Campagna",
        author_email="simone.campagna11@gmail.com",
        url="https://github.com/simone-campagna/invoice",
        download_url='https://github.com/simone-campagna/invoice/archive/{}.tar.gz'.format(VERSION),
        package_dir={'': 'src'},
        packages=find_packages("src"),
        package_data={'invoice.spy': ['icons/*.jpg']},
        entry_points={
            'console_scripts': [
                'invoice=invoice.invoice_main:invoice_main',
            ],
        },
    )

if __name__ == "__main__":
    main()
