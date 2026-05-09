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
