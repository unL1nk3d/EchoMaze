from abc import ABC, abstractmethod
from typing import List
from tunnelsManager.models.tunnel import Tunnel

class ForTunnelRepository(ABC):
    @abstractmethod
    def save_tunnel(self, tunnel: Tunnel) -> Tunnel:
        pass

    @abstractmethod
    def list_tunnels(self) -> List[Tunnel]:
        pass

    @abstractmethod
    def get_tunnel(self, tunnel_id: int) -> Tunnel:
        pass

    @abstractmethod
    def delete_tunnel(self, tunnel_id: int) -> bool:
        pass
