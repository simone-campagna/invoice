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
    'invoice_main'
]

import argparse
import os
import sys
import traceback

from .error import InvoiceSyntaxError
from .conf import VERSION, DB_FILE, DB_FILE_VAR
from .log import get_default_logger, set_verbose_level
from .invoice import Invoice
from .invoice_program import InvoiceProgram

def invoice_main(print_function=print, logger=None, args=None):
    if args is None:
        args = sys.argv[1:]
    if logger is None:
        logger = get_default_logger()

    all_field_names = []
    for field_name in Invoice._fields:
        all_field_names.append(field_name)
        n = InvoiceProgram.get_field_translation(field_name)
        if n != field_name:
            all_field_names.append(n)

    default_validate = True
    default_warnings_mode = InvoiceProgram.WARNINGS_MODE_DEFAULT
    default_list_field_names = InvoiceProgram.LIST_FIELD_NAMES_LONG
    default_filters = []

    def type_fields(s):
        field_names = []
        for field_name in s.split(','):
            field_name = field_name.strip()
            if not field_name in InvoiceProgram.ALL_FIELDS:
                raise ValueError("campo {!r} non valido".format(field_name))
            field_names.append(field_name)
        return field_names

    def type_years_filter(s):
        years = tuple(int(y.strip()) for y in s.split(','))
        if len(years) == 1:
            filter_source = 'year == {}'.format(years[0])
        else:
            filter_source = 'year in {{{}}}'.format(', '.join(str(year) for year in years))
        return filter_source

    def type_onoff(value):
        if value.lower() in {"on", "true"}:
            return True
        elif value.lower() in {"off", "false"}:
            return False
        else:
            raise ValueError("valore {!r} non valido (i valori leciti sono on/True|off/False)".format(value))

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
%(prog)s {version} - legge e processa una collezione di file DOC
contenenti fatture.

La lettura del file DOC avviene attraverso il programma 'catdoc', che
deve quindi essere installato.

ATTENZIONE: attualmente è gestito un solo formato per le fatture; in
futuro, potrebbero essere supportati formati generici.
La directory 'example' contiene alcuni file di esempio.

Le fatture lette e processsate vengono archiviate in un database SQLite;
questo database è normalmente in

{db_filename}

Il comando 'init' inizializza il database; in questa fase vengono
fissate alcune opzioni, in particolare i pattern utilizzati per la
ricerca dei DOC file.

$ invoice -d x.db init 'example/*.doc' 

A questo punto, il comando 'scan' scansiona i DOC file presenti su
disco, legge i file nuovi o modificati di recente, esegue una
validazione delle fatture lette, ed archivia sul database i nuovi dati.

$ invoice -d x.db scan

Il contenuto del database può essere ispezionato utilizzando alcuni
comandi ('list', 'dump', 'report'). Ad esempio:

$ invoice -d x.db list --short
anno numero data       codice_fiscale   importo valuta
2014      1 2014-01-03 WNYBRC01G01H663Y   51.00 euro  
2014      2 2014-01-03 PRKPRT01G01H663Y   76.50 euro  
2014      3 2014-01-22 BNNBRC01G01H663Y  102.00 euro  
2014      4 2014-01-25 WNYBRC01G01H663Y   51.00 euro  
2014      5 2014-01-29 KNTCRK01G01H663Y  152.50 euro  

# modalità legacy
Questa modalità serve ad emulare il comportamento della versione 1.x di
%(prog)s; in tal caso, non viene utilizzato il database.

$ invoice legacy 'example/*.doc' -l
fattura:                  'example/2014_001_bruce_wayne.doc'
  anno/numero:            2014/1
  città/data:             Gotham City/2014-01-03
  nome:                   Bruce Wayne
  codice fiscale:         WNYBRC01G01H663Y
  importo:                51.00 [euro]
...

""".format(db_filename=DB_FILE_VAR, version=VERSION),
        epilog="",
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

    ### config ###
    config_parser = subparsers.add_parser(
        "config",
        parents=(common_parser, ),
        description="""\
Configure db.
""",
    )
    config_parser.set_defaults(
        function_name="db_config",
        function_arguments=('show', 'patterns', 'remove_orphaned', 'partial_update'),
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
        function_arguments=('filters', ),
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
        const=InvoiceProgram.LIST_FIELD_NAMES_SHORT,
        default=default_list_field_names,
        help="short listing")

    list_argument_group.add_argument("--long", "-l",
        dest="field_names",
        action="store_const",
        const=InvoiceProgram.LIST_FIELD_NAMES_LONG,
        default=default_list_field_names,
        help="long listing")

    list_argument_group.add_argument("--full", "-f",
        dest="field_names",
        action="store_const",
        const=InvoiceProgram.LIST_FIELD_NAMES_FULL,
        default=default_list_field_names,
        help="full listing")

    list_argument_group.add_argument("--fields", "-o",
        dest="field_names",
        type=type_fields,
        default=default_list_field_names,
        help="manually select fields, for instance 'year,number,tax_code' [{}]".format('|'.join(all_field_names)))

    ### config list option
    config_parser.add_argument("--show", "-s",
        action="store_true",
        default=False,
        help="show configuration")

    ### year filter option
    for parser in list_parser, dump_parser, legacy_parser, report_parser:
        parser.add_argument("--year", "-y",
            metavar="Y",
            dest="filters",
            type=type_years_filter,
            action="append",
            default=default_filters,
            help="filter invoices by year")

    ### generic filter option
    for parser in list_parser, dump_parser, legacy_parser:
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
            const=InvoiceProgram.WARNINGS_MODE_ERROR,
            default=default_warnings_mode,
            help="make all warnings into errors")

        parser.add_argument("--wignore", "-wi",
            dest="warnings_mode",
            action="store_const",
            const=InvoiceProgram.WARNINGS_MODE_IGNORE,
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
    for parser in init_parser, config_parser, scan_parser:
        #parser.add_argument("--remove-orphaned", "-O",
        #    metavar="on/off",
        #    type=type_onoff,
        #    const=type_onoff("on"),
        #    default=None,
        #    nargs='?',
        #    help="remove orphaned database entries (invoices whose DOC file was removed from disk)")
        parser.set_defaults(remove_orphaned=False)

        parser.add_argument("--partial-update", "-U",
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
            help='doc patterns')

    config_parser.add_argument("--add-pattern", "-p",
        metavar="P",
        dest="patterns",
        default=[],
        type=lambda x: ('+', x),
        help="add pattern")

    config_parser.add_argument("--remove-pattern", "-x",
        metavar="P",
        dest="patterns",
        default=[],
        type=lambda x: ('-', x),
        help="remove pattern")

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


    args = top_level_parser.parse_args(args)

    set_verbose_level(logger, args.verbose_level)

    ip = InvoiceProgram(
        db_filename=args.db_filename,
        logger=logger,
        print_function=print_function,
        trace=args.trace,
    )

    function_argdict = {}
    for argument in args.function_arguments:
        function_argdict[argument] = getattr(args, argument)

    function = getattr(ip, args.function_name)
    try:
        return function(**function_argdict)
    except InvoiceSyntaxError as err:
        if args.trace:
            traceback.print_exc()
        message, function_source, syntax_error = err.args[1:]
        logger.error("{}:".format(message))
        logger.error("    {}".format(function_source))
        logger.error("    {}".format(" " * max(0, syntax_error.offset - 1) + '^'))

    except Exception as err:
        if args.trace:
            traceback.print_exc()
        logger.error("{}: {}\n".format(type(err).__name__, err))

