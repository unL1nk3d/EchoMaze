import argparse
import os
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB
from GATHERINGDB.init_db import DatabaseInitializer
from UI.ui import run_ui
from UI.models import GenericModel,Themes
from core import Core, PORT_SERVICE_MAP
from commands import Commands

def build_core_stack():
    dao = GenericDAO()
    crud = CRUD_GATHERINGDB(dao)
    core = Core(crud, PORT_SERVICE_MAP)
    cmd = Commands(core)
    generic = GenericModel(repository=core, commands=cmd)
    return dao, crud, core, cmd, generic


def main(argv=None):
    parser = argparse.ArgumentParser(description='Launcher for the HTB workspace')
    parser.add_argument('--ui', action='store_true', help='Run the asciimatics UI')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database (create tables)')
    parser.add_argument('--import-from-nmap', action='store_true', help='Parse nmap_scan.gnmap (or file specified with --nmap-file) and import results')
    parser.add_argument('--nmap-file', type=str, default='nmap_scan.gnmap', help='Path to greppable nmap file')
    parser.add_argument('--reload-from-directory', action='store_true', help='Reload IPs from the current directory')

    args = parser.parse_args(argv)

    dao, crud, core, cmd, generic = build_core_stack()

    # initialize DB explicitly
    if args.init_db:
        DatabaseInitializer.initialize_db(dao=dao)
        print('[*] Database initialized')

    # import from nmap file
    if args.import_from_nmap:
        cmd.import_from_nmap_scan_file(args.nmap_file)
        print(f'[*] import_from_nmap_scan completed (file={args.nmap_file})')

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
        run_ui(generic)


if __name__ == '__main__':
    main()