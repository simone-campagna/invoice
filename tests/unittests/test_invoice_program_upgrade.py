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
    'TestInvoiceProgramUpgrade',
]

import datetime
import glob
import io
import os
import shutil
import tempfile
import unittest

from invoice.log import get_null_logger
#from invoice.log import get_default_logger, set_verbose_level
from invoice.error import InvoiceVersionError

from invoice.invoice_program import InvoiceProgram
from invoice.database.db_types import Path
from invoice.string_printer import StringPrinter
from invoice.version import Version, VERSION
from invoice.upgrade import Upgrader

class TestInvoiceProgramUpgrade(unittest.TestCase):
    def setUp(self):
        self.dirname = Path.db_to(os.path.join(os.path.dirname(__file__), '..', '..', 'example'))
        self.logger = get_null_logger()
        #self.logger = get_default_logger()
        #set_verbose_level(self.logger, 1)

    def test_InvoiceProgramInvalidVersion(self):
        with tempfile.NamedTemporaryFile() as db_file:
            p = StringPrinter()

            invoice_program = InvoiceProgram(
                db_filename=db_file.name,
                logger=self.logger,
                trace=False,
                printer=p,
            )

            p.reset()
            invoice_program.impl_init(
                patterns=[os.path.join(self.dirname, '*.doc')],
                reset=True,
                partial_update=True,
                remove_orphaned=True,
            )

            Upgrader.full_downgrade(db=invoice_program.db)
            
            p.reset()
            invoice_program.impl_version(
                upgrade=False,
            )
            self.assertEqual(p.string(), """\
versione del programma: {}
versione del database:  {}
""".format(VERSION, Version(2, 0, 0)))

            p.reset()
            with self.assertRaises(InvoiceVersionError) as cm:
                invoice_program.impl_list()
            
            p.reset()
            invoice_program.impl_version(
                upgrade=True,
            )
            self.assertEqual(p.string(), """\
versione del programma: {}
versione del database:  {}
upgrade...
versione del database:  {}
""".format(VERSION, Version(2, 0, 0), VERSION))

            final_version = Version(VERSION.major, VERSION.minor, VERSION.patch + 100)
            Upgrader.full_upgrade(db=invoice_program.db, final_version=final_version)

            p.reset()
            invoice_program.impl_version(
                upgrade=False,
            )
            self.assertEqual(p.string(), """\
versione del programma: {}
versione del database:  {}
""".format(VERSION, final_version))
