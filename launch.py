import argparse
import os
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB
from GATHERINGDB.init_db import DatabaseInitializer
from UI.ui import run_ui
from UI.models import GenericModel,Themes
from core.core import Core, PORT_SERVICE_MAP
from core.scoring import ScoringEngine
from commands import Commands
from cheatIngestor.core import IngestorUseCase
from cheatIngestor.adapters.drivers.DocumentIngestorImpl import DocumentIngestorImp
from cheatIngestor.adapters.drivens.RepositoryImpl import Repository
from cheatIngestor.adapters.drivers.Autocomplete import AutoCompleter
from cheatIngestor.models.repository import Configurator
from logimporter import LogImportManager, validate_import_params

def build_core_stack():
    dao = GenericDAO()
    crud = CRUD_GATHERINGDB(dao)
    core = Core(crud, PORT_SERVICE_MAP)
    cmd = Commands(core)
    # drivens 
    repository = Repository()
    configurator = Configurator(True, repository, dao)
    repository.initialize_repository(configurator)
    # drivers 
    auto = AutoCompleter(repository=repository)
    cli_ingestor = DocumentIngestorImp(repository=repository)
    
    ingestor_use_case = IngestorUseCase(documents=cli_ingestor,auto=auto)
    # Create ScoringEngine sharing the same CRUD instance as Core
    scoring_engine = ScoringEngine(crud=crud)
    generic = GenericModel(repository=core, commands=cmd, ingestor=auto, scoring_engine=scoring_engine)
    # Wire GenericModel as observer of ScoringEngine so score_changed events propagate to UI
    scoring_engine.attach(generic)
    return dao, crud, core, cmd, generic, cli_ingestor, auto, repository, scoring_engine

def main(argv=None):
    parser = argparse.ArgumentParser(description='Launcher for the HTB workspace')
    parser.add_argument('--ui', action='store_true', help='Run the asciimatics UI')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database (create tables)')
    parser.add_argument('--import-from-nmap', action='store_true', help='Parse nmap_scan.gnmap (or file specified with --nmap-file) and import results')
    parser.add_argument('--nmap-file', type=str, default='nmap_scan.gnmap', help='Path to greppable nmap file')
    parser.add_argument('--import-log', type=str, help='Import command history from a log file')
    parser.add_argument('--log-format', type=str, default=None, help='Log format (auto-detect if not specified). Formats: PlainText, JSON, JSONL, CSV, BashHistory, ZshHistory, PowerShellHistory')
    parser.add_argument('--log-operator', type=str, default=None, help='Operator name for imported commands')
    #parser.add_argument('--ingest', type=str, help='Ingest a JSON document for cheatsheets')
    parser.add_argument('--reload-from-directory', action='store_true', help='Reload IPs from the current directory')
    parser.add_argument('--search', type=str, help='Search for techniques by keyword')
    ingestor = parser.add_subparsers(title='ingestor',description='ingestor commands')
    i_sub = ingestor.add_parser('ingest')
    i_sub.add_argument('--document',help='json document to ingest see examples at the documentation')
    i_sub.add_argument('--drop',help='drop all data saved on the database',action='store_true')
    i_sub.add_argument('--list',help='list all templates saved on the database',action='store_true')
    
    
    
    
    args = parser.parse_args(argv)

    dao, crud, core, cmd, generic, cli_ingestor, auto, repository, scoring_engine = build_core_stack()

    # initialize DB explicitly
    if args.init_db:
        DatabaseInitializer.initialize_db(dao=dao)
        print('[*] Database initialized')

    # import from nmap file
    if args.import_from_nmap:
        cmd.import_from_nmap_scan_file(args.nmap_file)
        print(f'[*] import_from_nmap_scan completed (file={args.nmap_file})')

    # import from log file
    if args.import_log:
        valid, error = validate_import_params(args.import_log, args.log_format)
        if not valid:
            print(f"[!] Import validation failed: {error}")
            exit(1)
        
        import_mgr = LogImportManager(crud=crud)
        imported_count, report = import_mgr.import_from_file(
            filepath=args.import_log,
            format_hint=args.log_format,
            operator=args.log_operator
        )
        print(report)
        print(f'[*] Imported {imported_count} commands from log file')

    # reload from directory
    if args.reload_from_directory:
        cmd.reload_from_directory()
        print('[*] reload_from_directory completed')
    # run UI if requested
    if args.ui:
        
        # make sure cached data is populated before UI
        _ = generic.cachered_ips
        #print(generic.mapper.value)
        #print(generic.mapper.value)
        
        if generic.mapper.value == []:
            print("[!] No data available to display in UI. Please import data first. using --import-from-nmap or --reload-from-directory")
            exit(1)
        print(type(generic))
        run_ui(generic)
    if hasattr(args,'document') and args.document:
        cli_ingestor.ingestJsonDocument(args.document)
        print('[*] Document ingested')

    # search techniques
    if hasattr(args,'search') and args.search:
        result = auto.searchCoincidence(args.search)
        print(f'[*] Search results: {result} {[ vars(x) for x in dict(vars(result))['templates']]}')
    if hasattr(args,'list') and args.list:
        [ print(vars(x)) for x in repository.select_all_templates()]


if __name__ == '__main__':
    main()