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

from .database.filecopy import tempcopy, nocopy
from .error import InvoiceSyntaxError
from .conf import VERSION, DB_FILE, DB_FILE_VAR
from .log import get_default_logger, set_verbose_level
from .invoice import Invoice
from .validation_result import ValidationResult
from .invoice_program import InvoiceProgram

def invoice_main(print_function=print, logger=None, args=None):
    if args is None:
        args = sys.argv[1:]
    if logger is None:
        logger = get_default_logger()

    all_field_names = []
    for field_name in Invoice._fields:
        all_field_names.append(field_name)
        n = Invoice.get_field_translation(field_name)
        if n != field_name:
            all_field_names.append(n)

    default_validate = True
    default_warning_mode = ValidationResult.WARNING_MODE_DEFAULT
    default_error_mode = ValidationResult.ERROR_MODE_DEFAULT
    default_list_field_names = InvoiceProgram.LIST_FIELD_NAMES_LONG
    default_filters = []

    def type_fields(s):
        field_names = []
        for field_name in s.split(','):
            field_name = field_name.strip()
            if not field_name in Invoice.ALL_FIELDS:
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
        help="file contenete il database")

    common_parser.add_argument("--verbose", "-v",
        dest="verbose_level",
        action="count",
        default=0,
        help="aumenta il livello di verbosità")

    common_parser.add_argument("--dry-run", "-D",
        action="store_true",
        default=False,
        help="dry run (il database non viene modificato)")

    common_parser.add_argument('--version',
        action='version',
        version='%(prog)s {}'.format(VERSION),
        help='mostra la versione ed esce')

    common_parser.add_argument("--trace", "-t",
        action="store_true",
        default=False,
        help="in caso di errori, mostra un traceback")

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
        parents=(common_parser, ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = top_level_parser.add_subparsers()

    ### init_parser ###
    init_parser = subparsers.add_parser(
        "init",
        parents=(common_parser, ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Inizializza il database. Deve essere fornito almeno un pattern, ad
esempio:
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Accesso alla configurazione del database. Questo comando permette di
vedere configurazione e pattern (opzione --show/-s) e/o di modificarli.
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Esegue una scansione alla ricerca di DOC di fattura nuovi o modificati
di recente. Le fatture trovate vengono lette, validate, ed (in caso di
successo) archiviate.
Le informazioni lette sono:
  * anno		(year)
  * numero		(number)
  * città		(city)
  * data		(date)
  * nome		(name)
  * codice_fiscale	(tax_code)
  * importo		(income)
  * valuta		(currency)

Le fatture lette vengono validate per riconoscere tipici errori, come:
  * errato ordinamento delle date
  * errata numerazione
  * informazioni mancanti

Se la validazione ha successo, le fatture vengono archiviate nel
database; alle successive scansioni non saranno lette, a meno che
il relativo DOC file non sia stato modificato.
""",
    )
    scan_parser.set_defaults(
        function_name="db_scan",
        function_arguments=('warning_mode', 'error_mode', 'remove_orphaned', 'partial_update'),
    )

    ### clear_parser ###
    clear_parser = subparsers.add_parser(
        "clear",
        parents=(common_parser, ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Rimuove tutte le fatture dal database.
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Esegue una validazione del contenuto del database.
""",
    )
    validate_parser.set_defaults(
        function_name="db_validate",
        function_arguments=('warning_mode', 'error_mode'),
    )

    ### list_parser ###
    list_parser = subparsers.add_parser(
        "list",
        parents=(common_parser, ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra una lista delle fatture contenute nel database.
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra tutti i dettagli delle fatture contenute nel database.
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra un report per anno delle fatture contenute nel database.

Per ciascun anno, vengono mostrate le seguenti informazioni:
 * numero di fatture
 * numero di clienti
 * per ciascun cliente:
   * numero di fatture
   * incasso totale
   * incasso percentuale
   * numero di settimane in cui è stata emessa fattura
   * elenco delle settimane in cui è stata emessa fattura
 * numero di settimane in  cui è stata emessa fattura
 * per ciascuna settimana:
   * numero di fatture
   * incasso totale
   * incasso percentuale
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Modalità 'legacy': emula l'interfaccia della versione 1.X di %(prog)s,
e non fa uso del db. Tutti i DOC di fattura vengono letti, processati
e validati.
""",
    )
    legacy_parser.set_defaults(
        function_name="legacy",
        function_arguments=('patterns', 'filters', 'validate', 'list', 'report', 'warning_mode', 'error_mode'),
    )

    ### list_mode option
    list_parser.add_argument("--no-header", "-H",
        dest="header",
        action="store_false",
        default=True,
        help="non mostra l'header")

    list_argument_group = list_parser.add_mutually_exclusive_group()
    list_argument_group.add_argument("--short", "-s",
        dest="field_names",
        action="store_const",
        const=InvoiceProgram.LIST_FIELD_NAMES_SHORT,
        default=default_list_field_names,
        help="lista breve (mostra i campi {}".format(','.join(InvoiceProgram.LIST_FIELD_NAMES_SHORT)))

    list_argument_group.add_argument("--long", "-l",
        dest="field_names",
        action="store_const",
        const=InvoiceProgram.LIST_FIELD_NAMES_LONG,
        default=default_list_field_names,
        help="lista lunga (mostra i campi {}".format(','.join(InvoiceProgram.LIST_FIELD_NAMES_LONG)))

    list_argument_group.add_argument("--full", "-f",
        dest="field_names",
        action="store_const",
        const=InvoiceProgram.LIST_FIELD_NAMES_FULL,
        default=default_list_field_names,
        help="lista lunga (mostra i tutti i campi: {}".format(','.join(InvoiceProgram.LIST_FIELD_NAMES_FULL)))

    list_argument_group.add_argument("--fields", "-o",
        dest="field_names",
        type=type_fields,
        default=default_list_field_names,
        help="selezione manuale dei campi, ad esempio 'anno,codice_fiscale,città' [{}]".format('|'.join(all_field_names)))

    ### config list option
    config_parser.add_argument("--show", "-s",
        action="store_true",
        default=False,
        help="mostra la configurazione del database")

    ### year filter option
    for parser in list_parser, dump_parser, legacy_parser, report_parser:
        parser.add_argument("--year", "-y",
            metavar="Y",
            dest="filters",
            type=type_years_filter,
            action="append",
            default=default_filters,
            help="filtra le fatture in base all'anno")

    ### generic filter option
    for parser in list_parser, dump_parser, legacy_parser:
        parser.add_argument("--filter", "-F",
            metavar="F",
            dest="filters",
            type=str,
            action="append",
            default=default_filters,
            help="aggiunge un filtro sulle fatture (ad esempio 'anno == 2014')")

    ### warnings and error options
    for parser in scan_parser, validate_parser, legacy_parser:
        parser.add_argument("--werror", "-we",
            dest="warning_mode",
            action="store_const",
            const=ValidationResult.WARNING_MODE_ERROR,
            default=default_warning_mode,
            help="converte warning in errori")

        parser.add_argument("--wignore", "-wi",
            dest="warning_mode",
            action="store_const",
            const=ValidationResult.WARNING_MODE_IGNORE,
            default=default_warning_mode,
            help="ignora gli warning")

        parser.add_argument("--eraise", "-er",
            dest="error_mode",
            action="store_const",
            const=ValidationResult.ERROR_MODE_RAISE,
            default=default_error_mode,
            help="rende fatale il primo errore incontrato (per default, %(prog)s tenta di continuare)")
    
    ### reset option
    init_parser.add_argument("--reset", "-r",
        action="store_true",
        default=False,
        help="elimina il database se già esistente")

    ### partial_update option
    for parser in init_parser, config_parser, scan_parser:
        #parser.add_argument("--remove-orphaned", "-O",
        #    metavar="on/off",
        #    type=type_onoff,
        #    const=type_onoff("on"),
        #    default=None,
        #    nargs='?',
        #    help="abilita/disabilita la rimozione dal database le fatture 'orphane', ovvero quelle il cui documento è stato rimosso dal disco")
        parser.set_defaults(remove_orphaned=False)

        parser.add_argument("--partial-update", "-U",
            metavar="on/off",
            type=type_onoff,
            const=type_onoff("on"),
            default=None,
            nargs='?',
            help="abilita/disabilita l'update parziale del database (in caso di errori di validazione, l'update parziale fa in modo che le fatture corrette vengano comunque archiviate)")

    ### patterns option
    for parser in init_parser, legacy_parser:
        parser.add_argument("patterns",
            nargs='+',
            help='pattern per la ricerca dei DOC delle fatture')

    config_parser.add_argument("--add-pattern", "-p",
        metavar="P",
        dest="patterns",
        default=[],
        action="append",
        type=lambda x: ('+', x),
        help='aggiunge un pattern per la ricerca dei DOC delle fatture')

    config_parser.add_argument("--remove-pattern", "-x",
        metavar="P",
        dest="patterns",
        default=[],
        action="append",
        type=lambda x: ('-', x),
        help='rimuove un pattern per la ricerca dei DOC delle fatture')

    ### legacy options
    legacy_parser.add_argument("--disable-validation", "-V",
        dest="validate",
        action="store_false",
        default=default_validate,
        help="non esegue la validazione delle fatture")

    legacy_action_group = legacy_parser.add_mutually_exclusive_group()

    legacy_action_group.add_argument("--list", "-l",
        action="store_true",
        default=False,
        help="mostra tutte le fatture")

    legacy_action_group.add_argument("--report", "-r",
        action="store_true",
        default=False,
        help="mostra un report delle fatture per anno")


    args = top_level_parser.parse_args(args)

    set_verbose_level(logger, args.verbose_level)

    if args.dry_run:
        file_context_manager = tempcopy
    else:
        file_context_manager = nocopy

    with file_context_manager(args.db_filename) as fcm:
        ip = InvoiceProgram(
            db_filename=fcm.get_filename(),
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

