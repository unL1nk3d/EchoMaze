from UI.ui import demo
from UI.models import UIMapper,GenericModel,RepositoryModel
from asciimatics.screen import Screen
# Datos simulados
ip_data = [
    ("192.168.1", "172.16.1", ["SMB", "FTP", "SSH"]),
    ("10.0.0.5", "172.16.1", ["HTTP", "DNS"]),
    ("192.168.2", "172.16.2", ["RDP", "Telnet"]),
    ("10.0.0.6", "172.16.2", ["SMTP", "POP3"]),
    ("172.16.2","10.0.0.6", [])
]


parent_ips ={ 
    "172.16.1":["SMB"],
    "172.16.2": ["RDP", "ftp"],
    "10.0.0.6": []
    }

    
# Datos simulados
protocols = ["SMB", "FTP", "SSH", "HTTP", "DNS", "RDP", "Telnet", "SMTP", "POP3", "IMAP", "LDAP", "SNMP"]



model = UIMapper()
lst = []
for ip, parent_ip, protocols in ip_data:
    # Simula la creación de IPNode y su exportación
    class IPNode:
        def __init__(self, ip, parent_ip, protocols):
            self.ip = ip
            self.parent_ip = parent_ip
            self.protocols = protocols
        def exportAsTupple(self):
            return (self.ip, self.parent_ip, self.protocols)
    lst.append(IPNode(ip, parent_ip,[]))
class DummyRepository:
    def select_all_ips(self):
        return lst
    def select_all_ports(self):
        rst = []
        for x in ip_data:
            ip, parent_ip, protocols = x
            for protocol in protocols:
                rst.append(type('Ports', (object,), {'ip':ip,'port': protocol, 'service_name': protocol})())
        return rst
generic = GenericModel(repository=DummyRepository, commands=None)

generic.cachered_ips

print(generic.cachered_ips)
try:
    Screen.wrapper(func=demo,arguments=(generic,))
except KeyboardInterrupt:
    exit(0)