import argparse
import os
import sys
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

from auth.composition_root import bootstrap_auth
from auth.adapters.drivers.passwordAuthenticator import PasswordCredential
import getpass

def build_core_stack(session_manager=None):
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

    # Tunnels infrastructure
    from tunnelsManager.adapters.drivens.RepositoryImpl import InMemoryTunnelRepository
    from tunnelsManager.adapters.drivens.ConnectionTestImpl import NetworkConnectionTester
    from tunnelsManager.core import TunnelsUseCase
    
    tunnels_repo = InMemoryTunnelRepository()
    connection_tester = NetworkConnectionTester()
    tunnels_usecase = TunnelsUseCase(tunnels_repo, connection_tester)

    generic = GenericModel(
        repository=core, 
        commands=cmd, 
        ingestor=auto, 
        scoring_engine=scoring_engine, 
        session_manager=session_manager,
        tunnels_usecase=tunnels_usecase
    )
    # Wire GenericModel as observer of ScoringEngine so score_changed events propagate to UI
    scoring_engine.attach(generic)
    return dao, crud, core, cmd, generic, cli_ingestor, auto, repository, scoring_engine


def handle_import_ops(crud, import_ops_args):
    """
    Manejar importación de operaciones/comandos desde archivo.
    
    Args:
        crud: Instancia de CRUD_GATHERINGDB
        import_ops_args: Namespace con argumentos de import-ops
    """
    filepath = import_ops_args.file
    format_hint = import_ops_args.format
    operator = import_ops_args.operator
    node_id = import_ops_args.node_id
    
    # Validar parámetros
    valid, error = validate_import_params(filepath, format_hint)
    if not valid:
        print(f"[!] Validation failed: {error}")
        return False
    
    # Importar
    import_mgr = LogImportManager(crud=crud)
    imported_count, report = import_mgr.import_from_file(
        filepath=filepath,
        format_hint=format_hint,
        operator=operator,
        node_id=node_id
    )
    
    # Mostrar reporte
    print(report)
    print(f"[+] Successfully imported {imported_count} operations/commands")
    return True


def handle_import_nmap(cmd, nmap_file):
    """Manejar importación desde nmap."""
    try:
        cmd.import_from_nmap_scan_file(nmap_file)
        print(f'[+] Nmap import completed (file={nmap_file})')
        return True
    except Exception as e:
        print(f"[!] Nmap import failed: {str(e)}")
        return False


def handle_reload_directory(cmd):
    """Manejar recarga desde directorio."""
    try:
        cmd.reload_from_directory()
        print('[+] Reload from directory completed')
        return True
    except Exception as e:
        print(f"[!] Directory reload failed: {str(e)}")
        return False

def handle_login(iam, password_auth, session_manager):
    print("--- EchoMaze Login ---")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    creds = PasswordCredential(username, password)
    token = iam.authenticator(password_auth, creds)
    
    if token:
        session_manager.set_session(token)
        print(f"[+] Login successful as {username}")
        return True
    else:
        print("[!] Login failed")
        return False

def handle_forced_password_change(iam, session_manager):
    print("[!] SECURITY POLICY: You must change your password before proceeding.")
    while True:
        new_password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm new password: ")
        if new_password == confirm:
            if len(new_password) < 4:
                print("[!] Password too short.")
                continue
            
            if iam.change_password(session_manager.current_token, new_password):
                print("[+] Password changed successfully. Please log in again.")
                session_manager.clear_session()
                return True
            else:
                print("[!] Error updating password.")
                return False
        else:
            print("[!] Passwords do not match.")

import uuid
from auth.core.domain.user import User

def handle_register(iam, session_manager, register_args):
    if not session_manager.is_authenticated():
        print("[!] You must be logged in as an administrator to register new users.")
        return False
    
    if session_manager.current_token.restricted:
        print("[!] Your session is restricted. Please change your password first.")
        return False

    new_user = User(
        user_id=str(uuid.uuid4()),
        username=register_args.username,
        roles=register_args.roles.split(','),
        is_admin=register_args.admin,
        password=register_args.password,
        requires_password_change=True
    )
    
    if iam.create_user(session_manager.current_token, new_user):
        print(f"[+] User {register_args.username} registered successfully.")
        return True
    return False

def handle_initial_setup(iam):
    user_repo = iam.user_repo
    if not user_repo.get_user_by_username("admin"):
        print("[!] No administrator account detected.")
        print("[*] Starting initial EchoMaze setup...")
        while True:
            password = getpass.getpass("Set password for 'admin' user: ")
            confirm = getpass.getpass("Confirm password: ")
            if password == confirm:
                if len(password) < 4:
                    print("[!] Password too short. Use at least 4 characters.")
                    continue
                
                admin_user = User(
                    user_id=str(uuid.uuid4()),
                    username="admin",
                    roles=["admin"],
                    is_admin=True,
                    password=password
                )
                user_repo.save_user(admin_user)
                print("[+] Administrator account 'admin' created successfully.")
                break
            else:
                print("[!] Passwords do not match. Try again.")

def main(argv=None):
    parser = argparse.ArgumentParser(
        description='EchoMaze - Penetration Testing Database & Workflow Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py --ui                              # Start UI
  python launch.py --import-ops --file history.log   # Import command history
  python launch.py register --username op1 --password secret --roles operator
        """
    )
    
    # Global options
    parser.add_argument('--ui', action='store_true', help='Run the asciimatics UI')
    parser.add_argument('--login', action='store_true', help='Force login before proceeding')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database (create tables)')
    parser.add_argument('--reload-from-directory', action='store_true', help='Reload IPs from the current directory')
    parser.add_argument('--search', type=str, help='Search for techniques by keyword')
    
    # Nmap import
    parser.add_argument('--import-from-nmap', action='store_true', help='Parse nmap_scan.gnmap (or file specified with --nmap-file) and import results')
    parser.add_argument('--nmap-file', type=str, default='nmap_scan.gnmap', help='Path to greppable nmap file')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # register subcommand
    register_parser = subparsers.add_parser('register', help='Register a new operator (requires admin login)')
    register_parser.add_argument('--username', required=True, help='New operator username')
    register_parser.add_argument('--password', required=True, help='New operator password')
    register_parser.add_argument('--roles', default='operator', help='Comma-separated roles (default: operator)')
    register_parser.add_argument('--admin', action='store_true', help='Set as administrator')
    
    # import-ops subcommand
    import_ops_parser = subparsers.add_parser(
        'import-ops',
        help='Import command histories/logs from various formats',
        description='Import operators command logs from external sources'
    )
    import_ops_parser.add_argument(
        '--file',
        required=True,
        help='Path to log file (required)'
    )
    import_ops_parser.add_argument(
        '--format',
        default=None,
        choices=['PlainText', 'JSON', 'JSONL', 'CSV', 'BashHistory', 'ZshHistory', 'PowerShellHistory'],
        help='Log format (auto-detect if not specified)'
    )
    import_ops_parser.add_argument(
        '--operator',
        default=None,
        help='Operator/user name for imported commands (optional)'
    )
    import_ops_parser.add_argument(
        '--node-id',
        type=int,
        default=None,
        help='Associate with specific IP node (optional)'
    )
    
    # ingest subcommand (cheatsheets)
    ingest_parser = subparsers.add_parser('ingest', help='Ingest cheatsheet templates')
    ingest_parser.add_argument('--document', help='JSON document to ingest')
    ingest_parser.add_argument('--drop', action='store_true', help='Drop all data saved on the database')
    ingest_parser.add_argument('--list', action='store_true', help='List all templates saved on the database')
    
    args = parser.parse_args(argv)

    # Build authentication infrastructure first
    iam, password_auth, session_manager = bootstrap_auth()

    # Build core infrastructure and inject session_manager
    dao, crud, core, cmd, generic, cli_ingestor, auto, repository, scoring_engine = build_core_stack(session_manager)

    # Initial setup if needed
    handle_initial_setup(iam)

    def check_restriction():
        if session_manager.is_authenticated() and session_manager.current_token.restricted:
            if not handle_forced_password_change(iam, session_manager):
                sys.exit(1)
            # Re-auth
            print("[*] Re-authentication required.")
            if not handle_login(iam, password_auth, session_manager):
                sys.exit(1)

    # ===== Handle global commands =====
    
    if args.login:
        if not handle_login(iam, password_auth, session_manager):
            sys.exit(1)
        check_restriction()

    # Initialize database
    if args.init_db:
        check_restriction()
        DatabaseInitializer.initialize_db(dao=dao)
        print('[+] Database initialized')

    # Import from nmap
    if args.import_from_nmap:
        check_restriction()
        handle_import_nmap(cmd, args.nmap_file)

    # Reload from directory
    if args.reload_from_directory:
        check_restriction()
        handle_reload_directory(cmd)
    
    # Run UI
    if args.ui:
        # Require login for UI as per specs
        if not session_manager.is_authenticated():
             if not handle_login(iam, password_auth, session_manager):
                 sys.exit(1)
        
        check_restriction()

        # Make sure cached data is populated before UI
        _ = generic.cachered_ips
        
        if generic.mapper.value == []:
            print("[!] No data available to display in UI. Please import data first using --import-from-nmap or --reload-from-directory")
            sys.exit(1)
        run_ui(generic)
    
    # Search techniques
    if args.search:
        check_restriction()
        result = auto.searchCoincidence(args.search)
        if result and hasattr(result, 'templates'):
            print(f'[+] Search results for "{args.search}":')
            for template in result.templates:
                print(f"  - {vars(template)}")
        else:
            print(f'[!] No results found for "{args.search}"')

    # ===== Handle subcommands =====
    
    # register subcommand
    if args.command == 'register':
        if not session_manager.is_authenticated():
             if not handle_login(iam, password_auth, session_manager):
                 sys.exit(1)
        check_restriction()
        handle_register(iam, session_manager, args)
    
    # import-ops subcommand
    if args.command == 'import-ops':
        check_restriction()
        handle_import_ops(crud, args)
    
    # ingest subcommand
    elif args.command == 'ingest':
        check_restriction()
        if args.document:
            cli_ingestor.ingestJsonDocument(args.document)
            print('[+] Document ingested')
        
        if args.drop:
            print('[!] Drop functionality not yet implemented')
        
        if args.list:
            templates = repository.select_all_templates()
            if templates:
                print(f'[+] {len(templates)} templates found:')
                for t in templates:
                    print(f"  - {vars(t)}")
            else:
                print('[*] No templates found')


if __name__ == '__main__':
    main()
