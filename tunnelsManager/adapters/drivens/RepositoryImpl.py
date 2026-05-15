from typing import List
from tunnelsManager.ports.drivens.forTunnelRepository import ForTunnelRepository
from tunnelsManager.models.tunnel import Tunnel
import uuid

class InMemoryTunnelRepository(ForTunnelRepository):
    # ... (existing implementation)
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

    def get_tunnel(self, tunnel_id: int) -> Tunnel:
        return self._tunnels.get(tunnel_id)

    def delete_tunnel(self, tunnel_id: int) -> bool:
        if tunnel_id in self._tunnels:
            del self._tunnels[tunnel_id]
            return True
        return False

from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.model import TunnelDB, ImplantDB
from tunnelsManager.ports.drivens.forImplantRepository import ForImplantRepository
from tunnelsManager.models.implant import Implant

class DatabaseTunnelRepository(ForTunnelRepository):
    # ... (existing DatabaseTunnelRepository code)
    def __init__(self, dao: GenericDAO):
        self.dao = dao

    def _to_domain(self, db_tunnel: TunnelDB) -> Tunnel:
        if not db_tunnel: return None
        return Tunnel(
            id=db_tunnel.id,
            source_ip=db_tunnel.source_ip,
            dest_ip=db_tunnel.dest_ip,
            local_port=db_tunnel.local_port,
            remote_port=db_tunnel.remote_port,
            status=db_tunnel.status,
            technique=db_tunnel.technique,
            phase=db_tunnel.phase,
            tunnel_type=db_tunnel.tunnel_type,
            data_sent_bytes=db_tunnel.data_sent_bytes,
            data_received_bytes=db_tunnel.data_received_bytes,
            last_activity=db_tunnel.last_activity,
            entropy_score=db_tunnel.entropy_score,
            entropy_warning=db_tunnel.entropy_warning,
            data_type=db_tunnel.data_type
        )

    def _to_db(self, tunnel: Tunnel) -> TunnelDB:
        return TunnelDB(
            id=tunnel.id,
            source_ip=tunnel.source_ip,
            dest_ip=tunnel.dest_ip,
            local_port=tunnel.local_port,
            remote_port=tunnel.remote_port,
            status=tunnel.status,
            technique=tunnel.technique,
            phase=tunnel.phase,
            tunnel_type=tunnel.tunnel_type,
            data_sent_bytes=tunnel.data_sent_bytes,
            data_received_bytes=tunnel.data_received_bytes,
            last_activity=tunnel.last_activity,
            entropy_score=tunnel.entropy_score,
            entropy_warning=tunnel.entropy_warning,
            data_type=tunnel.data_type
        )

    def save_tunnel(self, tunnel: Tunnel) -> Tunnel:
        db_tunnel = self._to_db(tunnel)
        if tunnel.id is None:
            self.dao.insertar(db_tunnel)
            all_tunnels = self.dao.seleccionar(TunnelDB)
            if all_tunnels:
                last_tunnel = max(all_tunnels, key=lambda x: x.id)
                tunnel.id = last_tunnel.id
        else:
            self.dao.actualizar(db_tunnel, tunnel.id)
        return tunnel

    def list_tunnels(self) -> List[Tunnel]:
        db_tunnels = self.dao.seleccionar(TunnelDB)
        return [self._to_domain(t) for t in db_tunnels]

    def get_tunnel(self, tunnel_id: int) -> Tunnel:
        db_tunnel = self.dao.seleccionarPorId(TunnelDB, tunnel_id)
        return self._to_domain(db_tunnel)

    def delete_tunnel(self, tunnel_id: int) -> bool:
        count = self.dao.eliminar(TunnelDB, tunnel_id)
        return count > 0

class DatabaseImplantRepository(ForImplantRepository):
    """
    Persistent implementation of the implant repository using GATHERINGDB.
    """
    def __init__(self, dao: GenericDAO):
        self.dao = dao

    def _to_domain(self, db_implant: ImplantDB) -> Implant:
        if not db_implant: return None
        return Implant(
            id=db_implant.id,
            name=db_implant.name,
            implant_type=db_implant.implant_type,
            payload=db_implant.payload,
            description=db_implant.description,
            created_at=db_implant.created_at
        )

    def _to_db(self, implant: Implant) -> ImplantDB:
        return ImplantDB(
            id=implant.id,
            name=implant.name,
            implant_type=implant.implant_type,
            payload=implant.payload,
            description=implant.description,
            created_at=implant.created_at
        )

    def save_implant(self, implant: Implant) -> Implant:
        db_implant = self._to_db(implant)
        if implant.id is None:
            self.dao.insertar(db_implant)
            all_implants = self.dao.seleccionar(ImplantDB)
            if all_implants:
                last_implant = max(all_implants, key=lambda x: x.id)
                implant.id = last_implant.id
        else:
            self.dao.actualizar(db_implant, implant.id)
        return implant

    def list_implants(self) -> List[Implant]:
        db_implants = self.dao.seleccionar(ImplantDB)
        return [self._to_domain(i) for i in db_implants]

    def get_implant(self, implant_id: int) -> Implant:
        db_implant = self.dao.seleccionarPorId(ImplantDB, implant_id)
        return self._to_domain(db_implant)

    def delete_implant(self, implant_id: int) -> bool:
        count = self.dao.eliminar(ImplantDB, implant_id)
        return count > 0

