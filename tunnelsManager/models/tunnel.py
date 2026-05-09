from dataclasses import dataclass
from typing import Optional

@dataclass
class Tunnel:
    id: Optional[int]
    source_ip: str
    dest_ip: Optional[str]
    local_port: int
    remote_port: Optional[int]
    status: str = "active" # active, disconnected

    @property
    def is_hanging(self) -> bool:
        """Un túnel colgante es aquel que no está relacionado a ninguna dirección IP destino."""
        return not self.dest_ip or self.dest_ip.strip() == ""
