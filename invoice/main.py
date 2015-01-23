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
    'invoice_program'
]

import argparse
import traceback

from .conf import VERSION
from .invoice_collection import InvoiceCollection
from .invoice_collection_reader import InvoiceCollectionReader
from .log import get_default_logger, set_verbose_level

def invoice_program():
    parser = argparse.ArgumentParser(
    description="""\
Read and process a collection of invoices.

Each input invoice is a DOC file.
The 'catdoc' tool is used to convert DOC files; it must be available.

For each DOC file, the following information is retrieved:
  * 'year'
  * 'number'
  * 'city'
  * 'date'
  * 'name'
  * 'tax_code'
  * 'income'
  * 'currency'

The read invoices are validated in order to detect typical errors, such
as:
  * wrong dates ordering
  * wrong numbering
  * missing information

The read invoices can then be filtered by passing some filtering
function, for instance:
  * -f 'number > 10'

It is then possible to apply an action to the parsed invoices:
* --list, -l: all the invoices are listed
* --report, -r: a per-year report is shown.

""",
        epilog="""\
Please, donate 10% of the total income to the author {!r}!
""".format(__author__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    default_validate = True
    default_warnings_mode = InvoiceCollection.WARNINGS_MODE_DEFAULT

    parser.add_argument("--filter", "-f",
        metavar="F",
        dest="filters",
        type=str,
        action="append",
        default=[],
        help="add a filter (e.g. 'year == 2014')")

    parser.add_argument("--disable-validation", "-V",
        dest="validate",
        action="store_false",
        default=default_validate,
        help="do not validate invoices")

    action_group = parser.add_mutually_exclusive_group()

    action_group.add_argument("--list", "-l",
        action="store_true",
        default=False,
        help="list invoices")

    action_group.add_argument("--report", "-r",
        action="store_true",
        default=False,
        help="show invoice report")

    parser.add_argument("--trace", "-t",
        action="store_true",
        default=False,
        help="show traceback on errors invoices")

    parser.add_argument("--werror", "-we",
        dest="warnings_mode",
        action="store_const",
        const=InvoiceCollection.WARNINGS_MODE_ERROR,
        default=default_warnings_mode,
        help="make all warnings into errors")

    parser.add_argument("--wignore", "-wi",
        dest="warnings_mode",
        action="store_const",
        const=InvoiceCollection.WARNINGS_MODE_IGNORE,
        default=default_warnings_mode,
        help="ignore warnings")

    parser.add_argument("--raise", "-R",
        dest="raise_on_error",
        action="store_true",
        default=False,
        help="make first error be fatal")

    parser.add_argument("--verbose", "-v",
        dest="verbose_level",
        action="count",
        default=0,
        help="increase verbose level")

    parser.add_argument('--version',
        action='version',
        version='%(prog)s {}'.format(VERSION))

    parser.add_argument("patterns",
        nargs='+',
        help='doc patterns',
    )

    args = parser.parse_args()

    logger = get_default_logger()
    set_verbose_level(logger, args.verbose_level)

    invoice_collection_reader = InvoiceCollectionReader(trace=args.trace)

    invoice_collection = invoice_collection_reader.read(*args.patterns)

    if args.validate is None:
        args.validate = any([args.report])

    try:
        if args.validate:
            logger.info("validating {} invoices...".format(len(invoice_collection)))
            result = invoice_collection.validate(warnings_mode=args.warnings_mode, raise_on_error=args.raise_on_error)
            if result['errors']:
                logger.error("found #{} errors - exiting".format(result['errors']))
                return 1
    
        if args.filters:
            logger.info("filtering {} invoices...".format(len(invoice_collection)))
            for filter_source in args.filters:
                logger.info("applying filter {!r} to {} invoices...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        
    
        if args.list:
            logger.info("listing {} invoices...".format(len(invoice_collection)))
            invoice_collection.list()
    
        if args.report:
            logger.info("producing report for {} invoices...".format(len(invoice_collection)))
            invoice_collection.report()
    
    except Exception as err:
        if args.trace:
            traceback.print_exc()
        logger.error("{}: {}\n".format(type(err).__name__, err))

    return 0
