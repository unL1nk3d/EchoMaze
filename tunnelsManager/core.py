from typing import List, Dict
from tunnelsManager.models.tunnel import Tunnel
from tunnelsManager.ports.drivers.forTunnelCreation import ForTunnelCreation
from tunnelsManager.ports.drivers.forTunnelManagement import ForTunnelManagement
from tunnelsManager.ports.drivers.forTunnelStadistics import ForTunnelStadistics
from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest
from tunnelsManager.ports.drivens.forTunnelRepository import ForTunnelRepository

class TunnelsUseCase(ForTunnelCreation, ForTunnelManagement, ForTunnelStadistics):
    def __init__(self, repository: ForTunnelRepository, connection_tester: ForConnectionTest):
        self.repository = repository
        self.connection_tester = connection_tester

    def create_tunnel(self, source_ip: str, local_port: int, dest_ip: str = None, remote_port: int = None) -> Tunnel:
        # Check if local port is actually open/available, but we save it anyway for tracking
        is_open = self.connection_tester.test_local_port_open(local_port)
        status = "active" if is_open else "disconnected"

        tunnel = Tunnel(
            id=None,
            source_ip=source_ip,
            dest_ip=dest_ip,
            local_port=local_port,
            remote_port=remote_port,
            status=status
        )
        return self.repository.save_tunnel(tunnel)

    def get_all_tunnels(self) -> List[Tunnel]:
        return self.repository.list_tunnels()

    def get_hanging_tunnels(self) -> List[Tunnel]:
        return [t for t in self.repository.list_tunnels() if t.is_hanging]

    def delete_tunnel(self, tunnel_id: int) -> bool:
        return self.repository.delete_tunnel(tunnel_id)

    def get_tunnel_stats(self) -> Dict[str, int]:
        all_tunnels = self.get_all_tunnels()
        hanging_tunnels = [t for t in all_tunnels if t.is_hanging]
        active_tunnels = [t for t in all_tunnels if t.status == "active"]

        return {
            "total": len(all_tunnels),
            "hanging": len(hanging_tunnels),
            "active": len(active_tunnels)
        }
