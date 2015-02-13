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
    'Test_invoice_main',
]

import datetime
import unittest

from invoice.log import get_null_logger
from invoice.invoice_main import invoice_main
from invoice.string_printer import StringPrinter
from invoice.ee import snow

class Test_invoice_main(unittest.TestCase):
    DUMP_OUTPUT = """\
fattura:                   '<DIRNAME>/2014_001_bruce_wayne.doc'
  anno/numero:             2014/1
  città/data:              Gotham City/2014-01-03
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663S
  importo:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_002_peter_parker.doc'
  anno/numero:             2014/2
  città/data:              New York City/2014-01-03
  nome:                    Peter B. Parker
  codice fiscale:          PRKPRT01G01H663M
  importo:                 76.50 [euro]
fattura:                   '<DIRNAME>/2014_003_bruce_banner.doc'
  anno/numero:             2014/3
  città/data:              Greenville/2014-01-22
  nome:                    Robert Bruce Banner
  codice fiscale:          BNNBRC01G01H663S
  importo:                 102.00 [euro]
fattura:                   '<DIRNAME>/2014_004_bruce_wayne.doc'
  anno/numero:             2014/4
  città/data:              Gotham City/2014-01-25
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663S
  importo:                 51.00 [euro]
fattura:                   '<DIRNAME>/2014_005_clark_kent.doc'
  anno/numero:             2014/5
  città/data:              Smallville/2014-01-29
  nome:                    Clark Kent
  codice fiscale:          KNTCRK01G01H663X
  importo:                 152.50 [euro]
"""
    REPORT_OUTPUT = """\
anno                       2014
  * incasso totale:        433.00
  * numero di fatture:     5
  * numero di clienti:     4
    + cliente:             WNYBRC01G01H663S (Bruce Wayne):
      numero di fatture:   2
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           1, 4

    + cliente:             PRKPRT01G01H663M (Peter B. Parker):
      numero di fatture:   1
      incasso totale:      76.50
      incasso percentuale: 17.67%
      settimane:           1

    + cliente:             BNNBRC01G01H663S (Robert Bruce Banner):
      numero di fatture:   1
      incasso totale:      102.00
      incasso percentuale: 23.56%
      settimane:           4

    + cliente:             KNTCRK01G01H663X (Clark Kent):
      numero di fatture:   1
      incasso totale:      152.50
      incasso percentuale: 35.22%
      settimane:           5

  * numero di settimane:   3
    + settimana:           1 [2014-01-01 -> 2014-01-05]:
      numero di fatture:   2
      giorni:              2014-01-03 VE[2]
      incasso totale:      127.50
      incasso percentuale: 29.45%

    + settimana:           4 [2014-01-20 -> 2014-01-26]:
      numero di fatture:   2
      giorni:              2014-01-22 ME[1], 2014-01-25 SA[1]
      incasso totale:      153.00
      incasso percentuale: 35.33%

    + settimana:           5 [2014-01-27 -> 2014-02-02]:
      numero di fatture:   1
      giorni:              2014-01-29 ME[1]
      incasso totale:      152.50
      incasso percentuale: 35.22%

"""

    def setUp(self):
        self.logger = get_null_logger()
        self.maxDiff = None

    def test_invoice_main_ee_snow_flakes(self):
        p = StringPrinter()

        snow.set_animation(delay=0.01, duration=0.1)
        snow.set_printer(p)

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "snow"]
        )

    def test_invoice_main_ee_snow_money(self):
        p = StringPrinter()

        snow.set_animation(delay=0.01, duration=0.1)
        snow.set_printer(p)

        p.reset()
        invoice_main(
            printer=p,
            logger=self.logger,
            args=["help", "money"]
        )
