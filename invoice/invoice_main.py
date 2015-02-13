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
import collections
import datetime
import os
import sys
import traceback

from .database.filecopy import tempcopy, nocopy
from .error import InvoiceSyntaxError
from . import conf
from .log import get_default_logger, set_verbose_level
from .invoice import Invoice
from .validation_result import ValidationResult
from .invoice_program import InvoiceProgram
from .invoice_db import InvoiceDb
from .stream_printer import StreamPrinter

def invoice_main(printer=StreamPrinter(sys.stdout), logger=None, args=None):
    if args is None:
        args = sys.argv[1:]
    if logger is None:
        logger = get_default_logger()

    def type_fields(s):
        field_names = []
        for field_name in s.split(','):
            field_name = field_name.strip()
            if not field_name in conf.ALL_FIELDS:
                raise ValueError("campo {!r} non valido".format(field_name))
            field_names.append(field_name)
        return tuple(Invoice.get_field_name_from_translation(field_name) for field_name in field_names)

    def type_years_filter(s):
        years = tuple(int(y.strip()) for y in s.split(','))
        if len(years) == 1:
            filter_source = 'year == {}'.format(years[0])
        else:
            filter_source = 'year in {{{}}}'.format(', '.join(str(year) for year in years))
        return filter_source

    DATE_FORMAT = "%Y-%m-%d"

    def type_date(s):
        return datetime.datetime.strptime(s, DATE_FORMAT).date()

    def type_onoff(value):
        if isinstance(value, str):
            if value.lower() in {"on", "true"}:
                return True
            elif value.lower() in {"off", "false"}:
                return False
            else:
                raise ValueError("valore {!r} non valido (i valori leciti sono on/True|off/False)".format(value))
        else:
            return value

    def switch_onoff(value):
        if value is None:
            return None
        else:
            return not type_onoff(value)

    def type_pattern(s):
        return InvoiceDb.make_pattern(s)

    all_field_names = []
    for field_name in Invoice._fields:
        all_field_names.append(field_name)
        n = Invoice.get_field_translation(field_name)
        if n != field_name:
            all_field_names.append(n)

    top_level_parser_name = 'main'
    default_validate = True
    default_filters = []
    default_dry_run = False
    default_trace = type_onoff(os.environ.get("INVOICE_TRACE", "off"))

    # configuration
    default_warning_mode = None
    default_error_mode = None
    default_partial_update = None
    default_remove_orphaned = None
    default_header = None
    default_total = None
    default_stats_group = None
    default_list_field_names = None

    common_parser = argparse.ArgumentParser(
        add_help=False,
    )

    common_parser.add_argument("--help", "-h",
        action="help",
        help="mostra questo help e termina")

    common_parser.add_argument("--db", "-d",
        metavar="F",
        dest="db_file",
        default=None,
        help="file contenente il database")

    common_parser.add_argument("--rc-dir", "-R",
        metavar="D",
        dest="rc_dir",
        default=None,
        help="directory di configurazione")

    common_parser.add_argument("--verbose", "-v",
        dest="verbose_level",
        action="count",
        default=0,
        help="aumenta il livello di verbosità")

    common_parser.add_argument("--dry-run", "-D",
        metavar="on/off",
        type=type_onoff,
        const=switch_onoff(default_dry_run),
        default=default_dry_run,
        nargs='?',
        help="abilita/disabilita la modalità 'dry run' (il database non viene modificato)")

    common_parser.add_argument('--version',
        action='version',
        version='%(prog)s {}'.format(conf.VERSION),
        help='mostra la versione ed esce')

    common_parser.add_argument("--trace", "-t",
        metavar="on/off",
        type=type_onoff,
        const=switch_onoff(default_trace),
        default=default_trace,
        nargs='?',
        help="abilita/disabilita il traceback in caso di errori (per debug)")

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

{db_file_expr}

Due variabili d'ambiente controllano questo path:
* {rc_dir_var} (default={rc_dir_expr}):
  directory contenente il db file
* {db_file_var} (default=[${rc_dir_var}/]{db_file_expr}):

Il comando 'init' inizializza il database; in questa fase vengono
fissate alcune opzioni, in particolare i pattern utilizzati per la
ricerca dei DOC file.

$ invoice -d x.db init 'example/*.doc' 

A questo punto, il comando 'scan' scansiona i DOC file presenti su
disco, legge i file nuovi o modificati di recente, esegue una
validazione delle fatture lette, ed archivia sul database i nuovi dati.

$ invoice -d x.db scan

Il contenuto del database può essere ispezionato utilizzando alcuni
comandi ('list', 'dump', 'report', 'stats'). Ad esempio:

$ invoice -d x.db list --short
anno numero data       codice_fiscale   importo valuta
2014      1 2014-01-03 WNYBRC01G01H663S   51.00 euro  
2014      2 2014-01-03 PRKPRT01G01H663M   76.50 euro  
2014      3 2014-01-22 BNNBRC01G01H663S  102.00 euro  
2014      4 2014-01-25 WNYBRC01G01H663S   51.00 euro  
2014      5 2014-01-29 KNTCRK01G01H663X  152.50 euro  

# modalità legacy
Questa modalità serve ad emulare il comportamento della versione 1.x di
%(prog)s; in tal caso, non viene utilizzato il database.

$ invoice legacy 'example/*.doc' -l
fattura:                   '/home/simone/Programs/Programming/invoice/example/2014_001_bruce_wayne.doc'
  anno/numero:             2014/1
  città/data:              Gotham City/2014-01-03
  nome:                    Bruce Wayne
  codice fiscale:          WNYBRC01G01H663S
  importo:                 51.00 [euro]
...

""".format(db_file_var=conf.DB_FILE_VAR,
           db_file_expr=conf.DB_FILE_EXPR,
           rc_dir_var=conf.RC_DIR_VAR,
           rc_dir_expr=conf.RC_DIR_EXPR,
           version=conf.VERSION),
        epilog="",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = top_level_parser.add_subparsers()

    parser_dict = collections.OrderedDict()
    parser_dict[top_level_parser_name] = top_level_parser

    top_level_parser.set_defaults(parser_dict=parser_dict)

    def add_subparser(subparsers, name, *n_args, **p_args):
        parser = subparsers.add_parser(name, *n_args, **p_args)
        parser_dict[name] = parser
        return parser

    ### help_parser ###
    help_parser = add_subparser(subparsers,
        "help",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Stampa l'help
""",
    )
    help_parser.set_defaults(
        function_name="program_help",
        parser=top_level_parser,
        function_arguments=('parser_dict', 'command'),
    )

    ### init_parser ###
    init_parser = add_subparser(subparsers,
        "init",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Inizializza il database. Deve essere fornito almeno un pattern, ad
esempio:

$ %(prog)s init 'docs/*.doc'

I pattern vengono utilizzati per la ricerca dei DOC file contenenti le
fatture.
È importante che il comando riceva un pattern e non la lista di file
corrispondenti alla sua espansione, altrimenti la ricerca non avverrà
in modo corretto. Pertanto:

$ %(prog)s init 'docs/*.doc'

è corretto, e fa in modo che le successive scansioni ispezionino tutti
i DOC file corrispondenti al pattern 'docs/*.doc'. Al contrario,

$ %(prog)s init docs/*.doc

inizializza il database con i nomi dei file che corrispondono *adesso*
al pattern '*.doc'; le successive scansioni ispezioneranno solo questi
file, e non nuovi file che corrispondono al pattern.

Durante questa fase possono anche essere fissati i valori dei parametri
di configurazione; vedi

$ %(prog)s config -h

per una spiegazione di questi valori
""",
    )
    init_parser.set_defaults(
        function_name="program_init",
        function_arguments=('patterns', 'reset',
                            'warning_mode', 'error_mode',
                            'remove_orphaned', 'partial_update',
                            'header', 'total',
                            'list_field_names', 'stats_group'),
    )

    ### version ###
    version_parser = add_subparser(subparsers,
        "version",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Permette di visualizzare la versione del programma e del database.
""",
    )
    version_parser.set_defaults(
        function_name="program_version",
        function_arguments=(),
    )

    ### config ###
    config_parser = add_subparser(subparsers,
        "config",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Permette di modificare e visualizzare i parametri di configurazione; la
visualizzazione avviene DOPO la modifica. I parametri attualmente
supportati sono:
 * warning_mode[={wm}]: gestione dei warning sollevati durante la
   scansione:
   - 'log': viene eseguito solo il log dei messaggi di warning
   - 'error': i warning vengono gestiti come errori 
   - 'ignore': i warning vengono ignorati
 * error_mode[={em}]: gestione degli errori sollevati durante la
   scansione:
   - 'log': viene eseguito solo il log dei messaggi di errore
   - 'raise': viene sollevata una eccezione ad ogni errore, che quindi
     interrompe la scansione
 * partial_update[={pu}]: in caso di errori durante la scansione, salva
   comunque nel database le fatture che non contengono errori;
 * remove_orphaned[={ro}]: se il documento relativo ad una fattura è
   stato cancellato da disco, viene eliminato il dato dal database
   (questo parametro non è modificabile in quanto la funzionalità non è
   completamente implementata)
 * header[={hd}]: mostra un header per i comandi 'list' e 'stats'
 * total[={tt}]: mostra la riga del TOTALE per il comando 'stats'
 * stats_group[={sg}]: raggruppamento preferito per il comando 'stats'
 * list_field_names[={fn}]:
   lista predefinita dei campi per il comando 'list'
""".format(
            wm=InvoiceDb.DEFAULT_CONFIGURATION.warning_mode,
            em=InvoiceDb.DEFAULT_CONFIGURATION.error_mode,
            pu=InvoiceDb.DEFAULT_CONFIGURATION.partial_update,
            ro=InvoiceDb.DEFAULT_CONFIGURATION.remove_orphaned,
            hd=InvoiceDb.DEFAULT_CONFIGURATION.header,
            tt=InvoiceDb.DEFAULT_CONFIGURATION.total,
            sg=InvoiceDb.DEFAULT_CONFIGURATION.stats_group,
            fn=','.join(InvoiceDb.DEFAULT_CONFIGURATION.list_field_names),
        ),
    )
    config_parser.set_defaults(
        function_name="program_config",
        function_arguments=('reset',
                            'warning_mode', 'error_mode',
                            'remove_orphaned', 'partial_update',
                            'header', 'total',
                            'list_field_names', 'stats_group'),
    )

    ### patterns ###
    patterns_parser = add_subparser(subparsers,
        "patterns",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Permette di modificare e visualizzare i pattern utilizzati per la
ricerca delle fatture su disco.  La visualizzazione avviene DOPO la
modifica.
""",
    )
    patterns_parser.set_defaults(
        function_name="program_patterns",
        function_arguments=('patterns', 'reset'),
    )

    ### scan_parser ###
    scan_parser = add_subparser(subparsers,
        "scan",
        parents=(common_parser, ),
        add_help=False,
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
        function_name="program_scan",
        function_arguments=('warning_mode', 'error_mode', 'remove_orphaned', 'partial_update'),
    )

    ### clear_parser ###
    clear_parser = add_subparser(subparsers,
        "clear",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Rimuove tutte le fatture dal database.
""",
    )
    clear_parser.set_defaults(
        function_name="program_clear",
        function_arguments=(),
    )

    ### validate_parser ###
    validate_parser = add_subparser(subparsers,
        "validate",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Esegue una validazione del contenuto del database.
""",
    )
    validate_parser.set_defaults(
        function_name="program_validate",
        function_arguments=('warning_mode', 'error_mode'),
    )

    ### list_parser ###
    list_parser = add_subparser(subparsers,
        "list",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra una lista delle fatture contenute nel database.
""",
    )
    list_parser.set_defaults(
        function_name="program_list",
        function_arguments=('filters', 'date_from', 'date_to', 'list_field_names', 'header'),
    )

    ### dump_parser ###
    dump_parser = add_subparser(subparsers,
        "dump",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra tutti i dettagli delle fatture contenute nel database.
""",
    )
    dump_parser.set_defaults(
        function_name="program_dump",
        function_arguments=('filters', 'date_from', 'date_to', ),
    )

    ### report_parser ###
    report_parser = add_subparser(subparsers,
        "report",
        parents=(common_parser, ),
        add_help=False,
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
        function_name="program_report",
        function_arguments=('filters', ),
    )

    ### stats_parser ###
    stats_parser = add_subparser(subparsers,
        "stats",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Mostra statistiche relative a determinati periodi di tempo,
eventualmente raggruppate per settimane o mesi.  Le fatture possono
essere selezionate utilizzando i filtri.

Tutte le fatture che fanno parte del periodo selezionato possono
essere raggruppate per
 * anno                   (--group=year/-gyear)
 * mese                   (--group=month/-gmonth) [default]
 * settimana              (--group=week/-gweek)
 * giorno della settimana (--group=weekday/-gweekday)
 * giorno                 (--group=day/-gday)
 * cliente                (--group=client/-gclient)
 * città                  (--group=city/-gcity)

Per i raggruppamenti anno/mese/settimana/giorno della settimana/giorno
vengono mostrati:
  * periodo di riferimento
  * data di inizio del periodo di riferimento
  * data di fine del periodo di riferimento
  * numero di clienti
  * numero di fatture
  * incasso totale
  * incasso percentuale

Per il raggruppamento cliente vengono mostrati:
  * codice fiscale del cliente
  * data di prima fattura per il cliente
  * data di ultima fattura per il cliente
  * nome del cliente
  * numero di fatture
  * incasso totale
  * incasso percentuale

Per il raggruppamento città vengono mostrati:
  * città
  * data di prima fattura per la città
  * data di ultima fattura per la città
  * numero di clienti
  * numero di fatture
  * incasso totale
  * incasso percentuale

""",
    )
    stats_parser.set_defaults(
        function_name="program_stats",
        function_arguments=('filters', 'date_from', 'date_to', 'stats_group', 'total'),
    )

    ### legacy_parser ###
    legacy_parser = add_subparser(subparsers,
        "legacy",
        parents=(common_parser, ),
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
Modalità 'legacy': emula l'interfaccia della versione 1.X di %(prog)s,
e non fa uso del db. Tutti i DOC di fattura vengono letti, processati
e validati.
""",
    )
    legacy_parser.set_defaults(
        function_name="legacy",
        function_arguments=('patterns', 'filters', 'date_from', 'date_to', 'validate', 'list', 'report', 'warning_mode', 'error_mode'),
    )

    ### help parser commands
    help_parser.add_argument("command",
        nargs='?',
        default=top_level_parser_name,
        help="comando di cui stampare l'help")

    ### list_mode option
    for parser in init_parser, config_parser, list_parser:
        parser.add_argument("--header", "-H",
            dest="header",
            metavar="on/off",
            type=type_onoff,
            const=switch_onoff(default_header),
            default=default_header,
            nargs='?',
            help="abilita/disabilita l'header")

    for parser in init_parser, config_parser, list_parser:
        list_argument_group = parser.add_mutually_exclusive_group()
        list_argument_group.add_argument("--short", "-s",
            dest="list_field_names",
            action="store_const",
            const=conf.LIST_FIELD_NAMES_SHORT,
            default=default_list_field_names,
            help="lista breve (mostra i campi {}".format(','.join(conf.LIST_FIELD_NAMES_SHORT)))
    
        list_argument_group.add_argument("--long", "-l",
            dest="list_field_names",
            action="store_const",
            const=conf.LIST_FIELD_NAMES_LONG,
            default=default_list_field_names,
            help="lista lunga (mostra i campi {}".format(','.join(conf.LIST_FIELD_NAMES_LONG)))
    
        list_argument_group.add_argument("--full", "-f",
            dest="list_field_names",
            action="store_const",
            const=conf.LIST_FIELD_NAMES_FULL,
            default=default_list_field_names,
            help="lista lunga (mostra i tutti i campi: {}".format(','.join(conf.LIST_FIELD_NAMES_FULL)))
    
        list_argument_group.add_argument("--fields", "-o",
            dest="list_field_names",
            type=type_fields,
            default=default_list_field_names,
            help="selezione manuale dei campi, ad esempio 'anno,codice_fiscale,città' [{}]".format('|'.join(all_field_names)))

    ### year filter option
    for parser in list_parser, dump_parser, legacy_parser, report_parser, stats_parser:
        parser.add_argument("--year", "-y",
            metavar="Y",
            dest="filters",
            type=type_years_filter,
            action="append",
            default=default_filters,
            help="filtra le fatture in base all'anno")

    ### generic filter option
    for parser in list_parser, dump_parser, legacy_parser, stats_parser:
        parser.add_argument("--start", "-S",
            metavar="S",
            dest="date_from",
            type=type_date,
            default=None,
            help="seleziona solo le fatture con data successiva o uguale a S")
    
        parser.add_argument("--end", "-E",
            metavar="E",
            dest="date_to",
            type=type_date,
            default=None,
            help="seleziona solo le fatture con data precedente o uguale a E")

    for parser in list_parser, dump_parser, legacy_parser, stats_parser:
        parser.add_argument("--filter", "-F",
            metavar="F",
            dest="filters",
            type=str,
            action="append",
            default=default_filters,
            help="aggiunge un filtro generico sulle fatture (ad esempio 'anno == 2014')")

    for parser in init_parser, config_parser, stats_parser:
        parser.add_argument("--group", "-g",
            dest="stats_group",
            choices=conf.STATS_GROUPS,
            default=default_stats_group,
            help="raggruppa le fatture per anno/mese/settimana/giorno/tutto il periodo")

    for parser in init_parser, config_parser, stats_parser:
        parser.add_argument("--total", "-T",
            dest="total",
            metavar="on/off",
            type=type_onoff,
            const=switch_onoff(default_total),
            default=default_total,
            nargs='?',
            help="abilita/disabilita il totale per l'intero periodo")

    ### warnings and error options
    for parser in init_parser, config_parser, scan_parser, validate_parser, legacy_parser:
        parser.add_argument("--warning-mode", "-w",
            dest="warning_mode",
            choices=ValidationResult.WARNING_MODES,
            default=default_warning_mode,
            help="modalità di gestione dei warning")

        parser.add_argument("--error-mode", "-e",
            dest="error_mode",
            choices=ValidationResult.ERROR_MODES,
            default=default_error_mode,
            help="modalità di gestione degli errori")

    ### reset options
    init_parser.add_argument("--reset", "-r",
        dest="reset",
        action="store_true",
        default=False,
        help="elimina il database se già esistente")

    config_parser.add_argument("--reset", "-r",
        dest="reset",
        default=False,
        action="store_true",
        help='ripristina la configuratione di default')

    patterns_parser.add_argument("--clear", "-c",
        dest="reset",
        default=False,
        action="store_true",
        help='rimuove tutti i pattern')

    ### partial_update option
    for parser in init_parser, config_parser, scan_parser:
        #parser.add_argument("--remove-orphaned", "-O",
        #    metavar="on/off",
        #    type=type_onoff,
        #    const=switch_onoff(default_remove_orphaned),
        #    default=default_remove_orphaned,
        #    nargs='?',
        #    help="abilita/disabilita la rimozione dal database le fatture 'orphane', ovvero quelle il cui documento è stato rimosso dal disco")
        parser.set_defaults(remove_orphaned=False)

        parser.add_argument("--partial-update", "-U",
            metavar="on/off",
            type=type_onoff,
            const=switch_onoff(default_partial_update),
            default=default_partial_update,
            nargs='?',
            help="abilita/disabilita l'update parziale del database (in caso di errori di validazione, l'update parziale fa in modo che le fatture corrette vengano comunque archiviate)")

    ### patterns option
    for parser in init_parser, legacy_parser:
        parser.add_argument("patterns",
            nargs='+',
            type=type_pattern,
            help='pattern per la ricerca dei DOC delle fatture')

    patterns_parser.add_argument("--add-pattern", "-p",
        metavar="P",
        dest="patterns",
        default=[],
        action="append",
        type=lambda x: ('+', type_pattern(x)),
        help='aggiunge un pattern per la ricerca dei DOC delle fatture')

    patterns_parser.add_argument("--remove-pattern", "-x",
        metavar="P",
        dest="patterns",
        default=[],
        action="append",
        type=lambda x: ('-', type_pattern(x)),
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

    conf.setup(
        rc_dir=args.rc_dir,
        db_file=args.db_file,
    )
    with file_context_manager(conf.get_db_file()) as fcm:
        invoice_program = InvoiceProgram(
            db_filename=fcm.get_filename(),
            logger=logger,
            printer=printer,
            trace=args.trace,
        )
    
        if not hasattr(args, 'function_name'):
            return invoice_program.program_missing_subcommand(parser=top_level_parser)

        function_argdict = {}
        for argument in args.function_arguments:
            function_argdict[argument] = getattr(args, argument)
    
        function = getattr(invoice_program, args.function_name)
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

