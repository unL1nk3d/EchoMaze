from abc import ABC, abstractmethod
from tunnelsManager.models.tunnel import Tunnel

class ForTunnelCreation(ABC):
    @abstractmethod
    def create_tunnel(self, source_ip: str, local_port: int, dest_ip: str = None, remote_port: int = None) -> Tunnel:
        """Crea y registra un nuevo túnel en el sistema."""
        pass
