from typing import List, Dict
from datetime import datetime
from tunnelsManager.models.tunnel import Tunnel
from tunnelsManager.ports.drivers.forTunnelCreation import ForTunnelCreation
from tunnelsManager.ports.drivers.forTunnelManagement import ForTunnelManagement
from tunnelsManager.ports.drivers.forTunnelStadistics import ForTunnelStadistics
from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest
from tunnelsManager.ports.drivens.forTunnelRepository import ForTunnelRepository
import core.entropy as entropy

class TunnelsUseCase(ForTunnelCreation, ForTunnelManagement, ForTunnelStadistics):
    def __init__(self, repository: ForTunnelRepository, connection_tester: ForConnectionTest):
        self.repository = repository
        self.connection_tester = connection_tester
        self.check_interval = 60 # Default interval in seconds

    def create_tunnel(self, source_ip: str, local_port: int, dest_ip: str = None, remote_port: int = None, tunnel_type: str = Tunnel.TYPE_HTTP, data_type: str = None, implant_id: int = None) -> Tunnel:
        # Check if local port is actually open/available, but we save it anyway for tracking
        is_open = self.connection_tester.test_local_port_open(local_port)
        status = Tunnel.STATUS_ACTIVE if is_open else Tunnel.STATUS_DISCONNECTED

        tunnel = Tunnel(
            id=None,
            source_ip=source_ip,
            dest_ip=dest_ip,
            local_port=local_port,
            remote_port=remote_port,
            status=status,
            phase=Tunnel.PHASE_CREATION,
            tunnel_type=tunnel_type,
            data_sent_bytes=0,
            data_received_bytes=0,
            last_activity=None,
            entropy_score=0.0,
            entropy_warning="Pending evaluation",
            data_type=data_type,
            implant_id=implant_id
        )
        return self.repository.save_tunnel(tunnel)

    def advance_tunnel_phase(self, tunnel_id: int) -> Tunnel:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if not tunnel:
            return None

        if tunnel.phase == Tunnel.PHASE_CREATION:
            return self.setup_tunnel(tunnel_id)
        elif tunnel.phase == Tunnel.PHASE_SETTING_UP:
            return self.register_interface(tunnel_id)
        elif tunnel.phase == Tunnel.PHASE_INTERFACE_REGISTRATION:
            return self.set_ready(tunnel_id)

        return tunnel

    def setup_tunnel(self, tunnel_id: int) -> Tunnel:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if tunnel and tunnel.phase == Tunnel.PHASE_CREATION:
            tunnel.phase = Tunnel.PHASE_SETTING_UP
            return self.repository.save_tunnel(tunnel)
        return tunnel

    def register_interface(self, tunnel_id: int) -> Tunnel:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if tunnel and tunnel.phase == Tunnel.PHASE_SETTING_UP:
            tunnel.phase = Tunnel.PHASE_INTERFACE_REGISTRATION
            return self.repository.save_tunnel(tunnel)
        return tunnel

    def set_ready(self, tunnel_id: int) -> Tunnel:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if tunnel and tunnel.phase == Tunnel.PHASE_INTERFACE_REGISTRATION:
            tunnel.phase = Tunnel.PHASE_READY_TO_SEND
            tunnel.status = Tunnel.STATUS_ACTIVE
            return self.repository.save_tunnel(tunnel)
        return tunnel

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

    def get_tunnel_stats(self) -> Dict[str, any]:
        all_tunnels = self.get_all_tunnels()
        
        # Auditor request: Use calcular_entropia on tunnel distribution
        tunnel_types_history = [t.tunnel_type for t in all_tunnels]
        # We need objects with 'comando' attribute or similar for calcular_entropia
        class DummyEvent:
            def __init__(self, t): self.comando = t
        
        history_objs = [DummyEvent(tt) for tt in tunnel_types_history]
        global_entropy = entropy.calcular_entropia(history_objs)
        entropy_warning = entropy.get_entropy_warning(global_entropy)

        stats = {
            "total": len(all_tunnels),
            "hanging": len([t for t in all_tunnels if t.is_hanging]),
            "active": len([t for t in all_tunnels if t.status == Tunnel.STATUS_ACTIVE]),
            "disconnected": len([t for t in all_tunnels if t.status == Tunnel.STATUS_DISCONNECTED]),
            "deactivated": len([t for t in all_tunnels if t.status == Tunnel.STATUS_DEACTIVATED]),
            "activating": len([t for t in all_tunnels if t.status == Tunnel.STATUS_ACTIVATING]),
            "filtered": len([t for t in all_tunnels if t.status == Tunnel.STATUS_FILTERED]),
            "global_entropy": global_entropy,
            "entropy_warning": entropy_warning
        }

        return stats

    def register_data_transfer(self, tunnel_id: int, sent_bytes: int, received_bytes: int) -> bool:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if not tunnel:
            return False
        
        tunnel.data_sent_bytes += sent_bytes
        tunnel.data_received_bytes += received_bytes
        tunnel.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.repository.save_tunnel(tunnel)
        return True

    def get_tunnel_metrics(self, tunnel_id: int) -> Dict[str, any]:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if not tunnel:
            return {}
        
        return {
            "sent_bytes": tunnel.data_sent_bytes,
            "received_bytes": tunnel.data_received_bytes,
            "last_activity": tunnel.last_activity
        }

    def evaluate_tunnel_entropy(self, tunnel_id: int) -> bool:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if not tunnel:
            return False
        
        # Priority: predefined data_type, then fallback to tunnel_type mapping
        if hasattr(tunnel, 'data_type') and tunnel.data_type in entropy.ENTROPY_DATA_TYPES:
            portador_type = tunnel.data_type
        else:
            # Map tunnel type to entropy data type (fallback)
            type_mapping = {
                Tunnel.TYPE_HTTP: 'texto plano',
                Tunnel.TYPE_IMAGE_TUNNEL: 'imagenes jpeg',
                Tunnel.TYPE_SHADOWSOCKS: 'datos cifrados',
                Tunnel.TYPE_STEGANOGRAPHY: 'post compresion data',
                Tunnel.TYPE_DNS: 'base64 encode',
                Tunnel.TYPE_ICMP: 'texto plano',
                Tunnel.TYPE_SOCKS4: 'datos cifrados',
                Tunnel.TYPE_SOCKS5: 'datos cifrados'
            }
            portador_type = type_mapping.get(tunnel.tunnel_type, 'texto plano')
        
        portador_size = tunnel.data_sent_bytes + tunnel.data_received_bytes
        
        # We evaluate if the current tunnel activity could hide a "Standard Exfiltration Package" (1KB of code)
        is_valid, message = entropy.evaluate_exfiltration(
            info_type='codigo fuente',
            info_size_bytes=1024,
            portador_type=portador_type,
            portador_size_bytes=max(portador_size, 1) # Avoid 0
        )
        
        tunnel.entropy_score = entropy.ENTROPY_DATA_TYPES.get(portador_type, 0.0)
        tunnel.entropy_warning = f"[{tunnel.tunnel_type} / {portador_type}] {message}"
        
        self.repository.save_tunnel(tunnel)
        return True

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

    def link_tunnel_to_implant(self, tunnel_id: int, implant_id: int) -> bool:
        tunnel = self.repository.get_tunnel(tunnel_id)
        if tunnel:
            tunnel.implant_id = implant_id
            self.repository.save_tunnel(tunnel)
            return True
        return False
