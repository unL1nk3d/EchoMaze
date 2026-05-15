from abc import ABC, abstractmethod
from tunnelsManager.models.tunnel import Tunnel

class ForTunnelCreation(ABC):
    @abstractmethod
    def create_tunnel(self, source_ip: str, local_port: int, dest_ip: str = None, remote_port: int = None, tunnel_type: str = Tunnel.TYPE_HTTP, data_type: str = None) -> Tunnel:
        """Phase 1: Tunnel Creation. Crea y registra un nuevo túnel en el sistema."""
        pass

    @abstractmethod
    def setup_tunnel(self, tunnel_id: int) -> Tunnel:
        """Phase 2: Tunnel Setting Up. Configura los parámetros iniciales del túnel."""
        pass

    @abstractmethod
    def register_interface(self, tunnel_id: int) -> Tunnel:
        """Phase 3: Interface Registration. Registra la interfaz de red asociada al túnel."""
        pass

    @abstractmethod
    def set_ready(self, tunnel_id: int) -> Tunnel:
        """Phase 4: Ready to Send. Marca el túnel como listo para enviar tráfico y lo activa."""
        pass

    @abstractmethod
    def advance_tunnel_phase(self, tunnel_id: int) -> Tunnel:
        """Avanza el túnel a la siguiente fase de creación de forma automática."""
        pass
