import os
from core import Core
from GATHERINGDB.init_db import DatabaseInitializer

class Commands:
    def __init__(self,core:Core=None):
        self.core = core
    def check_db_created(self):
        DatabaseInitializer.check_db_created(self.core,self.core.crud.dao)
    def import_from_nmap_scan(self):
        # default filename 'nmap_scan.gnmap' can be overridden by parameter
        return self.import_from_nmap_scan_file('nmap_scan.gnmap')

    def import_from_nmap_scan_file(self, nmap_file: str):
        """Import results from a greppable nmap file path."""
        ip_ports = self.core.parse_greppable_nmap(nmap_file)
        self.core.create_ip_directories(ip_ports, base_dir=os.getcwd())
        self.core.insert_ip_from_nmap(ip_ports=ip_ports)
        return ip_ports
        # este mismo comando debe de implementar una logica
        # para poder hacer un walk e ingresar dinamicamente a los directorios creados
        # para si el pentester realizo un escaneo entonces ir ahi y re mapear las nuevas direcciones ip
    def reload_from_directory(self):
        # implementar logica para recargar desde el directorio actual
        self.core.insert_ip_from_directory(os.getcwd())
        for directory,ip in self.core.detect_ip_directories(base_dir=os.getcwd()):
            self.core.insert_services_from_directory(directory,ip)