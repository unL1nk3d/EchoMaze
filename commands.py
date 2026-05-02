import os
from core.core import Core
from GATHERINGDB.init_db import DatabaseInitializer
from logimporter import LogImportManager

class Commands:
    def __init__(self,core:Core=None):
        self.core = core
        self.log_import_manager = LogImportManager(crud=core.crud) if core else None
    
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
    
    def import_logs(self, filepath: str, format_hint: str = None, operator: str = None, node_id: int = None):
        """
        Importar historiales de comandos desde un archivo.
        
        Args:
            filepath: Ruta del archivo de log
            format_hint: Formato del log (auto-detecta si es None)
            operator: Nombre del operador
            node_id: ID del nodo IP asociado
            
        Returns:
            Tupla de (cantidad_importada, report)
        """
        if not self.log_import_manager:
            raise RuntimeError("LogImportManager not initialized. Core required.")
        
        return self.log_import_manager.import_from_file(
            filepath=filepath,
            format_hint=format_hint,
            operator=operator,
            node_id=node_id
        )
