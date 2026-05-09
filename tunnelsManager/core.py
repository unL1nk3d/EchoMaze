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
        self.check_interval = 60 # Default interval in seconds

    def create_tunnel(self, source_ip: str, local_port: int, dest_ip: str = None, remote_port: int = None) -> Tunnel:
        # Check if local port is actually open/available, but we save it anyway for tracking
        is_open = self.connection_tester.test_local_port_open(local_port)
        status = Tunnel.STATUS_ACTIVE if is_open else Tunnel.STATUS_DISCONNECTED

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

    def update_tunnel_status(self, tunnel_id: int, new_status: str) -> bool:
        if new_status not in Tunnel.ALLOWED_STATUSES:
            return False
            
        tunnels = self.get_all_tunnels()
        for t in tunnels:
            if t.id == tunnel_id:
                t.status = new_status
                self.repository.save_tunnel(t)
                return True
        return False

    def get_tunnel_stats(self) -> Dict[str, int]:
        all_tunnels = self.get_all_tunnels()
        
        stats = {
            "total": len(all_tunnels),
            "hanging": len([t for t in all_tunnels if t.is_hanging]),
            "active": len([t for t in all_tunnels if t.status == Tunnel.STATUS_ACTIVE]),
            "disconnected": len([t for t in all_tunnels if t.status == Tunnel.STATUS_DISCONNECTED]),
            "deactivated": len([t for t in all_tunnels if t.status == Tunnel.STATUS_DEACTIVATED]),
            "activating": len([t for t in all_tunnels if t.status == Tunnel.STATUS_ACTIVATING]),
            "filtered": len([t for t in all_tunnels if t.status == Tunnel.STATUS_FILTERED])
        }

        return stats

    def set_connection_check_policy(self, interval_seconds: int):
        self.check_interval = interval_seconds

    def check_tunnels_health(self):
        """
        Iterates over all tunnels and updates their status based on connection test,
        except for those explicitly deactivated.
        """
        tunnels = self.get_all_tunnels()
        for t in tunnels:
            if t.status == Tunnel.STATUS_DEACTIVATED:
                continue
            
            is_open = self.connection_tester.test_local_port_open(t.local_port)
            new_status = Tunnel.STATUS_ACTIVE if is_open else Tunnel.STATUS_DISCONNECTED
            
            if t.status != new_status:
                t.status = new_status
                self.repository.save_tunnel(t)

    def activate_tunnel(self, tunnel_id: int) -> bool:
        """
        Sets a tunnel to active status.
        """
        return self.update_tunnel_status(tunnel_id, Tunnel.STATUS_ACTIVE)

    def set_activating_status(self, tunnel_id: int) -> bool:
        """
        Sets a tunnel to activating status.
        """
        return self.update_tunnel_status(tunnel_id, Tunnel.STATUS_ACTIVATING)

    def deactivate_tunnel(self, tunnel_id: int) -> bool:
        """
        Sets a tunnel to deactivated status.
        """
        return self.update_tunnel_status(tunnel_id, Tunnel.STATUS_DEACTIVATED)

    def set_tunnel_technique(self, tunnel_id: int, technique: str) -> bool:
        if technique not in Tunnel.ALLOWED_TECHNIQUES:
            return False
            
        tunnels = self.get_all_tunnels()
        for t in tunnels:
            if t.id == tunnel_id:
                t.technique = technique
                self.repository.save_tunnel(t)
                return True
        return False

    def process_implant_beacon(self, tunnel_id: int) -> bool:
        """
        Processes a beacon received from an implant.
        Status transitions:
        - activating/disconnected/filtered -> active (if technique is beaconing)
        - active -> active (acknowledged)
        - deactivated -> stays deactivated (ignored)
        """
        tunnels = self.get_all_tunnels()
        for t in tunnels:
            if t.id == tunnel_id:
                if t.status == Tunnel.STATUS_DEACTIVATED:
                    return False
                
                if t.technique == Tunnel.TECHNIQUE_BEACONING:
                    if t.status != Tunnel.STATUS_ACTIVE:
                        t.status = Tunnel.STATUS_ACTIVE
                        self.repository.save_tunnel(t)
                    return True
        return False
