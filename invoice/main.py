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

from .conf import VERSION, DB_FILENAME
from .log import get_default_logger, set_verbose_level
from .invoice_collection import InvoiceCollection
from .invoice_db import InvoiceDb

class InvoiceProgram(object):
    def __init__(self, db_filename, logger, trace):
        self.db_filename = db_filename
        self.logger = logger
        self.trace = trace
        self.db = InvoiceDb(self.db_filename, self.logger)

    def db_init(self, *, patterns):
        self.db.initialize()
        self.db.write('patterns', [InvoiceDb.Pattern(pattern=pattern) for pattern in patterns])

    def db_scan(self, *, warnings_mode, raise_on_error):
        invoice_collection = self.db.scan(warnings_mode=warnings_mode, raise_on_error=raise_on_error)

    def db_clear(self):
        self.db.delete('invoices')

    def db_validate(self, *, warnings_mode, raise_on_error):
        invoice_collection = self.db.load_invoice_collection()
        result = invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
        return result['errors']

    def db_list(self, *, filters):
        invoice_collection = self.db.load_invoice_collection()
        if filters:
            logger.info("filtering {} invoices...".format(len(invoice_collection)))
            for filter_source in filters:
                logger.info("applying filter {!r} to {} invoices...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        invoice_collection.list()

    def db_report(self):
        invoice_collection = self.db.load_invoice_collection()
        invoice_collection.report()

def invoice_program():
    default_validate = True
    default_warnings_mode = InvoiceCollection.WARNINGS_MODE_DEFAULT

    common_parser = argparse.ArgumentParser(
        add_help=False,
    )

    common_parser.add_argument("--db", "-d",
        dest="db_filename",
        default=DB_FILENAME,
        help="db filename")

    common_parser.add_argument("--verbose", "-v",
        dest="verbose_level",
        action="count",
        default=0,
        help="increase verbose level")

    common_parser.add_argument('--version',
        action='version',
        version='%(prog)s {}'.format(VERSION))

    common_parser.add_argument("--trace", "-t",
        action="store_true",
        default=False,
        help="show traceback on errors invoices")

    top_level_parser = argparse.ArgumentParser(
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
        parents=(common_parser, ),
    )

    subparsers = top_level_parser.add_subparsers()

    init_parser = subparsers.add_parser(
        "init",
        parents=(common_parser, ),
    )
    init_parser.set_defaults(
        function_name="db_init",
        function_arguments=('patterns', ),
    )

    init_parser.add_argument("patterns",
        nargs='+',
        help='doc patterns',
    )

    scan_parser = subparsers.add_parser(
        "scan",
        parents=(common_parser, ),
    )
    scan_parser.set_defaults(
        function_name="db_scan",
        function_arguments=('warnings_mode', 'raise_on_error'),
    )

    clear_parser = subparsers.add_parser(
        "clear",
        parents=(common_parser, ),
    )
    clear_parser.set_defaults(
        function_name="db_clear",
        function_arguments=(),
    )

    validate_parser = subparsers.add_parser(
        "validate",
        parents=(common_parser, ),
    )
    validate_parser.set_defaults(
        function_name="db_validate",
        function_arguments=('warnings_mode', 'raise_on_error'),
    )

    list_parser = subparsers.add_parser(
        "list",
        parents=(common_parser, ),
    )
    list_parser.set_defaults(
        function_name="db_list",
        function_arguments=('filters', ),
    )

    list_parser.add_argument("--filter", "-f",
        metavar="F",
        dest="filters",
        type=str,
        action="append",
        default=[],
        help="add a filter (e.g. 'year == 2014')")

    report_parser = subparsers.add_parser(
        "report",
        parents=(common_parser, ),
    )
    report_parser.set_defaults(
        function_name="db_report",
        function_arguments=(),
    )

    for parser in scan_parser, validate_parser:
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
    

    args = top_level_parser.parse_args()

    logger = get_default_logger()
    set_verbose_level(logger, args.verbose_level)

    ip = InvoiceProgram(
        db_filename=args.db_filename,
        logger=logger,
        trace=args.trace,
    )

    function_argdict = {}
    for argument in args.function_arguments:
        function_argdict[argument] = getattr(args, argument)

    function = getattr(ip, args.function_name)
    try:
        return function(**function_argdict)
    except Exception as err:
        if args.trace:
            traceback.print_exc()
        logger.error("{}: {}\n".format(type(err).__name__, err))

