import os
import re
from collections import defaultdict
from nmap_parser import parse_greppable_nmap, create_ip_directories
from WorkflowScreamer.makeWorkFlowDirectories import make_dirs

# Mapeo básico de puertos a servicios
PORT_SERVICE_MAP = {
    21: 'ftp',
    22: 'ssh',
    3389: 'rdp',
    80: 'http',
    443: 'https',
    139: 'smb',
    445: 'smb',
    3306: 'mysql',
    5432: 'postgres',
    25: 'smtp',
    110: 'pop3',
    143: 'imap'
}

def parse_greppable_nmap(file_path):
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

def create_ip_directories(ip_ports, base_dir='scan_results'):
    os.makedirs(base_dir, exist_ok=True)

    for ip, ports in ip_ports.items():
        ip_dir = os.path.join(base_dir, ip)
        os.makedirs(ip_dir, exist_ok=True)

        for port in ports:
            service = PORT_SERVICE_MAP.get(port, f'port_{port}')
            service_dir = os.path.join(ip_dir, service)
            os.makedirs(service_dir, exist_ok=True)

def main(file_path:str):
    #file_path = 'waves.gnmap'  # Cambia esto si tu archivo tiene otro nombre
    ip_ports = parse_greppable_nmap(file_path)
    create_ip_directories(ip_ports)

if __name__ == '__main__':
    main()
