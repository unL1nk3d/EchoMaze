from abc import ABC, abstractmethod
from typing import List
from tunnelsManager.models.tunnel import Tunnel

class ForTunnelManagement(ABC):
    @abstractmethod
    def get_all_tunnels(self) -> List[Tunnel]:
        """Obtiene todos los túneles registrados."""
        pass

    @abstractmethod
    def get_hanging_tunnels(self) -> List[Tunnel]:
        """Obtiene solo los túneles colgantes (sin IP destino)."""
        pass

    @abstractmethod
    def delete_tunnel(self, tunnel_id: int) -> bool:
        """Elimina un túnel registrado."""
        pass

    @abstractmethod
    def update_tunnel_status(self, tunnel_id: int, new_status: str) -> bool:
        """Actualiza el estado de un túnel."""
        pass

    @abstractmethod
    def set_connection_check_policy(self, interval_seconds: int):
        """Establece el intervalo de tiempo para comprobar la conexión de los túneles."""
        pass

    @abstractmethod
    def check_tunnels_health(self):
        """Ejecuta una comprobación de salud en todos los túneles activos."""
        pass

    @abstractmethod
    def activate_tunnel(self, tunnel_id: int) -> bool:
        """Activa manualmente un túnel."""
        pass

    @abstractmethod
    def set_activating_status(self, tunnel_id: int) -> bool:
        """Establece el estado de un túnel como 'activating'."""
        pass

    @abstractmethod
    def deactivate_tunnel(self, tunnel_id: int) -> bool:
        """Desactiva manualmente un túnel."""
        pass

    @abstractmethod
    def set_tunnel_technique(self, tunnel_id: int, technique: str) -> bool:
        """Establece la técnica que utilizará el implante para este túnel."""
        pass

    @abstractmethod
    def process_implant_beacon(self, tunnel_id: int) -> bool:
        """Procesa un beacon recibido de un implante para un túnel específico."""
        pass
