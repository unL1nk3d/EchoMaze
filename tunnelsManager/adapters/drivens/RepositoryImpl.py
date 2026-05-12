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
from GATHERINGDB.model import TunnelDB

class DatabaseTunnelRepository(ForTunnelRepository):
    """
    Persistent implementation of the tunnel repository using GATHERINGDB (SQLite).
    """
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
            entropy_warning=db_tunnel.entropy_warning
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
            entropy_warning=tunnel.entropy_warning
        )

    def save_tunnel(self, tunnel: Tunnel) -> Tunnel:
        db_tunnel = self._to_db(tunnel)
        if tunnel.id is None:
            # We don't have a direct way to get the inserted ID from GenericDAO.insertar currently 
            # as it returns rowcount. But GenericDAO is using autoincrement.
            # Usually we want the last_insert_rowid. 
            # Looking at GenericDAO.insertar, it returns cursor.rowcount.
            # This is a limitation in the current GATHERINGDB abstraction.
            # For now, let's assume we can query it back or that GenericDAO can be extended.
            # Actually, GenericDAO.insertar returns cursor.rowcount which is 1.
            self.dao.insertar(db_tunnel)
            # Find the last inserted tunnel to get the ID
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
