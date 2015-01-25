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
import os
import traceback

from .conf import VERSION, DB_FILE, DB_FILE_VAR
from .log import get_default_logger, set_verbose_level
from .invoice import Invoice
from .invoice_collection import InvoiceCollection
from .invoice_collection_reader import InvoiceCollectionReader
from .invoice_db import InvoiceDb

class InvoiceProgram(object):
    def __init__(self, db_filename, logger, trace):
        self.db_filename = db_filename
        self.logger = logger
        self.trace = trace
        self.db = InvoiceDb(self.db_filename, self.logger)

    def db_init(self, *, patterns, reset, partial_update, remove_orphaned):
        if reset and os.path.exists(self.db_filename):
            self.logger.info("removing db {!r}".format(self.db_filename))
            os.remove(self.db_filename)
        self.db.initialize()
        self.db.configure(
            patterns=patterns,
            remove_orphaned=remove_orphaned,
            partial_update=partial_update,
        )

    def db_scan(self, *, warnings_mode, raise_on_error, partial_update, remove_orphaned):
        self.db.check()
        invoice_collection = self.db.scan(
            warnings_mode=warnings_mode,
            raise_on_error=raise_on_error,
            partial_update=partial_update,
            remove_orphaned=remove_orphaned,
        )

    def db_clear(self):
        self.db.check()
        self.db.delete('invoices')

    def db_validate(self, *, warnings_mode, raise_on_error):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        validation_result = invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
        return validation_result.num_errors()

    def db_filter(self, invoice_collection, filters):
        self.db.check()
        if filters:
            self.logger.info("filtering {} invoices...".format(len(invoice_collection)))
            for filter_source in filters:
                self.logger.info("applying filter {!r} to {} invoices...".format(filter_source, len(invoice_collection)))
                invoice_collection = invoice_collection.filter(filter_source)
        return invoice_collection

    def db_list(self, *, field_names, header, filters):
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        invoice_collection.list(header=header, field_names=field_names)

    def db_dump(self, *, filters):
        self.db.check()
        invoice_collection = self.db_filter(self.db.load_invoice_collection(), filters)
        invoice_collection.dump()

    def db_report(self):
        self.db.check()
        invoice_collection = self.db.load_invoice_collection()
        invoice_collection.report()

    def legacy(self, patterns, filters, validate, list, report, warnings_mode, raise_on_error):
        invoice_collection_reader = InvoiceCollectionReader(trace=self.trace)

        invoice_collection = invoice_collection_reader.read(*patterns)

        if validate is None:
            validate = any([report])

        try:
            if validate:
                self.logger.info("validating {} invoices...".format(len(invoice_collection)))
                validation_result = invoice_collection.validate(warnings_mode=warnings_mode, raise_on_error=raise_on_error)
                if validation_result.num_errors():
                    self.logger.error("found #{} errors - exiting".format(validation_result.num_errors()))
                    return 1
    
            invoice_collection = self.db_filter(invoice_collection, filters)
    
            if list:
                self.logger.info("listing {} invoices...".format(len(invoice_collection)))
                invoice_collection.dump()
    
            if report:
                self.logger.info("producing report for {} invoices...".format(len(invoice_collection)))
                invoice_collection.report()
    
        except Exception as err:
            if self.trace:
                traceback.print_exc()
            self.logger.error("{}: {}\n".format(type(err).__name__, err))

def invoice_program():
    default_validate = True
    default_warnings_mode = InvoiceCollection.WARNINGS_MODE_DEFAULT
    default_list_field_names = InvoiceCollection.LIST_FIELD_NAMES_LONG
    default_filters = []

    def type_fields(s):
        field_names = []
        for field_name in s.split(','):
            field_name = field_name.strip()
            if not field_name in Invoice._fields:
                raise ValueError("invalid field {!r}".format(field_name))
            field_names.append(field_name)
        return field_names

    def type_years_filter(s):
        years = tuple(int(y.strip()) for y in s.split(','))
        if len(years) == 1:
            filter_source = 'year == {}'.format(years[0])
        else:
            filter_source = 'year in {{{}}}'.format(', '.join(str(year) for year in years))
        print("{!r} -> {!r}".format(s, filter_source))
        return filter_source

    def type_onoff(value):
        if value.lower() in {"on", "true"}:
            return True
        elif value.lower() in {"off", "false"}:
            return False
        else:
            raise ValueError("invalid on/off value {!r} (accepts on/True|off/False".format(value))

    common_parser = argparse.ArgumentParser(
        add_help=False,
    )

    common_parser.add_argument("--db", "-d",
        metavar="F",
        dest="db_filename",
        default=DB_FILE,
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
%(prog)s {version}  - read and process a collection of invoices.

Each input invoice is a DOC file.
The 'catdoc' tool is used to convert DOC files; it must be available.

WARNING: currently a single invoice formatting is supported, so this
tool is not really usable. In the future, generic invoice formatting
will be supported.
The example directory contains some example invoices.

The read invoices are stored on a SQLite3 db; sqlite3 python module must be
available.

The db is normally stored in
{db_filename}

The init subcommand is used to initialize the db; then, the 'scan'
subcommand can be used to read new or recently changed invoice DOC
files. Other subcommands ('list', 'report') can be used to show some
information about the invoices stored on the db.

$ invoice -d x.db init 'example/*.doc' 
$ invoice -d x.db scan
$ invoice -d x.db list --short
year number date       tax_code         income currency
2014      1 2014-01-03 WNYBRC01G01H663Y  51.00 euro    
2014      2 2014-01-03 PRKPRT01G01H663Y  76.00 euro    
2014      3 2014-01-22 WNYBRC01G01H663Y 102.00 euro    
2014      4 2014-01-25 WNYBRC01G01H663Y  51.00 euro    
2014      5 2014-01-29 PRKPRT01G01H663Y  76.00 euro    

[legacy mode]

$ invoice legacy 'example/*.doc' -l
invoice:                  'example/2014_001_bruce_wayne.doc'
  year/number:            2014/1
  city/date:              Gotham City/2014-01-03
  name:                   Bruce Wayne
  tax code:               WNYBRC01G01H663Y
  total income:           51.00 [euro]
...

""".format(db_filename=DB_FILE_VAR, version=VERSION),
        epilog="""\
Please, donate 10% of the your income to the author of this nice tool!
""".format(__author__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=(common_parser, ),
    )

    subparsers = top_level_parser.add_subparsers()

    ### init_parser ###
    init_parser = subparsers.add_parser(
        "init",
        parents=(common_parser, ),
        description="""\
Initialize the db. At least one pattern must be provided, for instance:
$ %(prog)s init 'docs/*.doc'
""",
    )
    init_parser.set_defaults(
        function_name="db_init",
        function_arguments=('patterns', 'reset', 'remove_orphaned', 'partial_update'),
    )

    ### scan_parser ###
    scan_parser = subparsers.add_parser(
        "scan",
        parents=(common_parser, ),
        description="""\
Read new or recently updated invoice DOC files and retrieves the
following information:
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

If validation is successfull, the read invoices are stored onto the db.
""",
    )
    scan_parser.set_defaults(
        function_name="db_scan",
        function_arguments=('warnings_mode', 'raise_on_error', 'remove_orphaned', 'partial_update'),
    )

    ### clear_parser ###
    clear_parser = subparsers.add_parser(
        "clear",
        parents=(common_parser, ),
        description="""\
Remove all invoices stored on the db.
""",
    )
    clear_parser.set_defaults(
        function_name="db_clear",
        function_arguments=(),
    )

    ### validate_parser ###
    validate_parser = subparsers.add_parser(
        "validate",
        parents=(common_parser, ),
        description="""\
Validate the invoices stored on the db.
""",
    )
    validate_parser.set_defaults(
        function_name="db_validate",
        function_arguments=('warnings_mode', 'raise_on_error'),
    )

    ### list_parser ###
    list_parser = subparsers.add_parser(
        "list",
        parents=(common_parser, ),
        description="""\
List the invoices stored on the db.
""",
    )
    list_parser.set_defaults(
        function_name="db_list",
        function_arguments=('filters', 'field_names', 'header'),
    )

    ### dump_parser ###
    dump_parser = subparsers.add_parser(
        "dump",
        parents=(common_parser, ),
        description="""\
Dump the content of the db.
""",
    )
    dump_parser.set_defaults(
        function_name="db_dump",
        function_arguments=('filters', ),
    )

    ### report_parser ###
    report_parser = subparsers.add_parser(
        "report",
        parents=(common_parser, ),
        description="""\
Show a report about the invoices stored on the db.
""",
    )
    report_parser.set_defaults(
        function_name="db_report",
        function_arguments=(),
    )

    ### legacy_parser ###
    legacy_parser = subparsers.add_parser(
        "legacy",
        parents=(common_parser, ),
        description="""\
Legacy mode: it has the same interface as the 1.0 version, and does not
use the db.
""",
    )
    legacy_parser.set_defaults(
        function_name="legacy",
        function_arguments=('patterns', 'filters', 'validate', 'list', 'report', 'warnings_mode', 'raise_on_error'),
    )

    ### list_mode option
    list_parser.add_argument("--no-header", "-H",
        dest="header",
        action="store_false",
        default=True,
        help="do not show header")

    list_argument_group = list_parser.add_mutually_exclusive_group()
    list_argument_group.add_argument("--short", "-s",
        dest="field_names",
        action="store_const",
        const=InvoiceCollection.LIST_FIELD_NAMES_SHORT,
        default=default_list_field_names,
        help="short listing")

    list_argument_group.add_argument("--long", "-l",
        dest="field_names",
        action="store_const",
        const=InvoiceCollection.LIST_FIELD_NAMES_LONG,
        default=default_list_field_names,
        help="long listing")

    list_argument_group.add_argument("--full", "-f",
        dest="field_names",
        action="store_const",
        const=InvoiceCollection.LIST_FIELD_NAMES_FULL,
        default=default_list_field_names,
        help="full listing")

    list_argument_group.add_argument("--fields", "-o",
        dest="field_names",
        type=type_fields,
        default=default_list_field_names,
        help="manually select fields, for instance 'year,number,tax_code' [{}]".format('|'.join(Invoice._fields)))

    ### year and filter option
    for parser in list_parser, dump_parser, legacy_parser:
        parser.add_argument("--year", "-y",
            metavar="Y",
            dest="filters",
            type=type_years_filter,
            action="append",
            default=default_filters,
            help="filter invoices by year")

        parser.add_argument("--filter", "-F",
            metavar="F",
            dest="filters",
            type=str,
            action="append",
            default=default_filters,
            help="add a filter (e.g. 'year == 2014')")

    ### warnings and error options
    for parser in scan_parser, validate_parser, legacy_parser:
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
    
    ### reset option
    init_parser.add_argument("--reset", "-r",
        action="store_true",
        default=False,
        help="reset db if it already exists")

    ### partial_update option
    for parser in init_parser, scan_parser:
        parser.add_argument("--remove-orphaned", "-O",
            metavar="on/off",
            type=type_onoff,
            const=type_onoff("on"),
            default=None,
            nargs='?',
            help="remove orphaned database entries (invoices whose DOC file was removed from disk)")

        parser.add_argument("--partial-update", "-P",
            metavar="on/off",
            type=type_onoff,
            const=type_onoff("on"),
            default=None,
            nargs='?',
            help="enable/disable partial update (in case of validation errors, correct invoices are added)")

    ### patterns option
    for parser in init_parser, legacy_parser:
        parser.add_argument("patterns",
            nargs='+',
            help='doc patterns',
        )

    ### legacy options
    legacy_parser.add_argument("--disable-validation", "-V",
        dest="validate",
        action="store_false",
        default=default_validate,
        help="do not validate invoices")

    legacy_action_group = legacy_parser.add_mutually_exclusive_group()

    legacy_action_group.add_argument("--list", "-l",
        action="store_true",
        default=False,
        help="list invoices")

    legacy_action_group.add_argument("--report", "-r",
        action="store_true",
        default=False,
        help="show invoice report")


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

