from typing import List
from tunnelsManager.ports.drivens.forTunnelRepository import ForTunnelRepository
from tunnelsManager.models.tunnel import Tunnel
import uuid

class InMemoryTunnelRepository(ForTunnelRepository):
    """
    Implementación sencilla en memoria para guardar los túneles,
    ya que GATHERINGDB no tiene una tabla específica para Túneles actualmente.
    En un paso posterior se podría integrar con CRUD_GATHERINGDB si se expande el modelo.
    """
    def __init__(self):
        self._tunnels = {}
        self._id_counter = 1

    def save_tunnel(self, tunnel: Tunnel) -> Tunnel:
        if tunnel.id is None:
            tunnel.id = self._id_counter
            self._id_counter += 1
        self._tunnels[tunnel.id] = tunnel
        return tunnel

    def list_tunnels(self) -> List[Tunnel]:
        return list(self._tunnels.values())

    def delete_tunnel(self, tunnel_id: int) -> bool:
        if tunnel_id in self._tunnels:
            del self._tunnels[tunnel_id]
            return True
        return False
