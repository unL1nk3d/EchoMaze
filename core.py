from GATHERINGDB.main import CRUD_GATHERINGDB,GenericDAO,log
from GATHERINGDB.model import IntegrityError
from GATHERINGDB.init_db import DatabaseInitializer
from collections import defaultdict

import re
import os
PORT_SERVICE_MAP = {
    21: 'ftp',
    22: 'ssh',
    23: 'telnet',
    25: 'smtp',
    53: 'dns',
    67: 'dhcp',
    68: 'dhcp',
    69: 'tftp',
    80: 'http',
    110: 'pop3',
    111: 'rpcbind',
    123: 'ntp',
    135: 'msrpc',
    137: 'netbios-ns',
    138: 'netbios-dgm',
    139: 'smb',
    143: 'imap',
    161: 'snmp',
    162: 'snmptrap',
    179: 'bgp',
    443: 'https',
    445: 'smb',
    465: 'smtps',
    514: 'syslog',
    587: 'submission',
    631: 'ipp',
    993: 'imaps',
    995: 'pop3s',
    1080: 'socks',
    1433: 'mssql',
    1521: 'oracle',
    1723: 'pptp',
    2049: 'nfs',
    3306: 'mysql',
    3389: 'rdp',
    5432: 'postgres',
    5900: 'vnc',
    6000: 'x11',
    6667: 'irc',
    8000: 'http-alt',
    8080: 'http-proxy',
    8443: 'https-alt',
    8888: 'sun-answerbook',
}



class Core:
    def __init__(self,crud:CRUD_GATHERINGDB=None,PORT_SERVICE_MAP:dict[int,str]=None):
        self.crud = crud
        self.port_service_map = PORT_SERVICE_MAP
    def select_all_ips(self):
        return self.crud.select_all_ips(dao=self.crud.dao)
    def select_all_ports(self):
        return self.crud.select_all_ports(dao=self.crud.dao)
    def detect_ip_directories(self,base_dir='scan_results'):
        ip_dirs = []
        if not os.path.exists(base_dir):
            return ip_dirs
        for entry in os.listdir(base_dir):
            full_path = os.path.join(base_dir, entry)
            if os.path.isdir(full_path):
                # validar si el nombre del directorio es una IP válida
                m = re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', entry)
                if m:
                    ip_dirs.append(( full_path,entry))
        return ip_dirs
    def insert_ip_from_directory(self,current_path, parent_ip=None,level = 0):
        if not os.path.exists(current_path):
            return

        for entry in os.listdir(current_path):
            full_path = os.path.join(current_path, entry)
            if not os.path.isdir(full_path):
                continue

            # buscar un posible IPv4 en el nombre (p. ej. "192.168.15.1" o "host-192.168.1.5")
            m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', entry)
            log.info(f'DEBUG ENTRY: {entry} IP match: {m.group(1) if m else None}')

            if m:
                ip = m.group(1)
                # validar rangos de octetos 0-255
                try:
                    octets = [int(o) for o in ip.split('.')]
                except ValueError:
                    log.info(f'Invalid IP format in entry: {entry} -> {ip}')
                    # aún descendemos para buscar IPs más adentro
                    parent_ip = ip
                    self.insert_ip_from_directory(full_path, parent_ip, level + 1)
                    continue

                if any(o < 0 or o > 255 for o in octets):
                    log.info(f'IP octet out of range in entry: {entry} -> {ip}')
                    # aún descendemos para buscar IPs más adentro
                    parent_ip = ip
                    self.insert_ip_from_directory(full_path, parent_ip, level + 1)
                    continue

                log.info(f'[+] Inserting IP from directory: {ip} at path: {full_path}')
                if not self.check_already_inserted_ip(ip):
                    try:
                        self.crud.insert_ip(entry, full_path, parent_ip, level, dao=self.crud.dao)
                    except IntegrityError:
                        log.info(f'IP {ip} already exists (integrity), skipping insert')

                # recorrer servicios dentro de este directorio IP
                self.insert_services_from_directory(full_path, ip)
            else:
                log.debug(f'No IP in dir name: {entry}, descendiendo para buscar en su interior')

            # Siempre descendemos en subdirectorios para detectar IPs hijas aunque el nombre
            # del subdirectorio actual no contenga una IP directamente.
            self.insert_ip_from_directory(full_path, parent_ip if m is None else ip, level + 1)
    def resolve_service_name(self,service_name:str) -> str|int:
        """
            si no resuelve el nombre del servicio retorna el puerto para que no se pierdan los datos
            
        """
        if len(service_name.split(".")) != 1:
           return # ITS AN IP  
        if service_name.isnumeric():
            return int(service_name)
        port = None
        
        for p, s in self.port_service_map.items():
            if s == service_name:
                port = p
                break
        return port
    def insert_services_from_directory(self,current_path, ip:str):
        for entry in os.listdir(current_path):
            log.info(f'DEBUG SERVICE ENTRY: {current_path} at path: {entry} {ip}')
            full_path = os.path.join(current_path, entry)
            if os.path.isdir(full_path):
                service_name:str = entry
                
                port = self.resolve_service_name(service_name=service_name)
                
                if port:
                    ip_e = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
                    if len(ip_e) == 0:
                        continue
                    ip_f = ip_e[0]
                    port_cek = self.check_already_inserted_port(ip_f.ip, port)
                    log.warning(f'PORT CHECK: {port_cek} for IP {ip_f.ip} and port {port}')
                    if port_cek:
                        continue
                    log.info(f'[+] Inserting port {port} ({service_name}) for IP {ip_f.ip}')
                    self.crud.insert_port_node(ip_f.id, port,self.port_service_map.get(port,None) or port,dao=self.crud.dao)
                self.insert_services_from_directory(full_path, ip)
    def check_already_inserted_ip(self,ip):
        ip_chk = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
        if len(ip_chk) > 0:
            return True
        return False
    def check_already_inserted_port(self,ip,chk_port):
        ip_entity = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
        log.info(f"DEBUG_PORT {ip_entity}")
        #if not(ip_entity):
        #    return False
        ip_entity = ip_entity[0]
        port_chk = self.crud.select_port_by_field('ip', ip_entity.ip, dao=self.crud.dao)
        log.warning(f'pc {port_chk}')
        for port in port_chk:
            if port.port == chk_port:
                return True
        #log.info(f"ports acquired {port_chk} {port} {type(chk_port)}")
        return False
    def insert_ip_from_nmap(self,ip_ports):
        # tested 
        for ip, ports in ip_ports.items():
            #ip_chk = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
            #log.error(f"CHECK: {ip_chk}")
            if self.check_already_inserted_ip(ip): 
                continue# IP already exists
            try:
                self.crud.insert_ip(ip, os.path.join(os.getcwd(),ip), '', dao=self.crud.dao)
            except Exception as e:
                print(f"[-] error inserting ip \n {e}")
            # should invoke this method at the commands
            self.insert_ports_from_nmap(ip,ports)
    def filter_ip(self,ip):
        return self.crud.select_ip_by_field('ip',ip,dao=self.crud.dao)
    
    def insert_ports_from_nmap(self,ip,ports):
        # tested  
        for port in ports:
            ip_entity = self.crud.select_ip_by_field('ip', ip, dao=self.crud.dao)
            if not(len(ip_entity)):
                continue
            
            log.warning(f'IP ERROR: {ip_entity}')
            ip_entity = ip_entity[0]
            self.crud.insert_port_node(ip_entity.id, port,self.port_service_map.get(port,None) or port, dao=self.crud.dao)
    def parse_greppable_nmap(self,file_path):
        ip_ports = defaultdict(list)

        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('Host:'):
                    match_ip = re.search(r'Host:\s+([\d\.]+)', line)
                    match_ports = re.findall(r'(\d+)/open', line)

                    if match_ip:
                        ip = match_ip.group(1)
                        ports = [int(p) for p in match_ports]
                        ip_ports[ip].extend(ports)

        return ip_ports
    def create_ip_directories(self,ip_ports, base_dir='scan_results'):
        os.makedirs(base_dir, exist_ok=True)

        for ip, ports in ip_ports.items():
            ip_dir = os.path.join(base_dir, ip)
            os.makedirs(ip_dir, exist_ok=True)

            for port in ports:
                service = self.port_service_map.get(port, f'{port}')
                service_dir = os.path.join(ip_dir, service)
                os.makedirs(service_dir, exist_ok=True)