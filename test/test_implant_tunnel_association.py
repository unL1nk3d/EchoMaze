import unittest
from tunnelsManager.models.tunnel import Tunnel
from tunnelsManager.models.implant import Implant
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.implants_core import ImplantsUseCase
from tunnelsManager.adapters.drivens.RepositoryImpl import InMemoryTunnelRepository
from tunnelsManager.ports.drivens.forImplantRepository import ForImplantRepository
from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest

class MockImplantRepository(ForImplantRepository):
    def __init__(self):
        self.implants = {}
        self.counter = 1
    def save_implant(self, implant):
        if not implant.id:
            implant.id = self.counter
            self.counter += 1
        self.implants[implant.id] = implant
        return implant
    def list_implants(self): return list(self.implants.values())
    def get_implant(self, id): return self.implants.get(id)
    def delete_implant(self, id): 
        if id in self.implants:
            del self.implants[id]
            return True
        return False

class MockConnectionTester(ForConnectionTest):
    def test_local_port_open(self, port: int) -> bool: return True

class TestImplantTunnelAssociation(unittest.TestCase):
    def setUp(self):
        self.tunnel_repo = InMemoryTunnelRepository()
        self.implant_repo = MockImplantRepository()
        self.conn_tester = MockConnectionTester()
        
        self.tunnels_usecase = TunnelsUseCase(self.tunnel_repo, self.conn_tester)
        self.implants_usecase = ImplantsUseCase(self.implant_repo)

    def test_implant_with_supported_tunnel_type(self):
        """Test that an implant can be created with a supported tunnel type."""
        implant = self.implants_usecase.create_implant(
            name="DNS_Exfil",
            implant_type=Implant.TYPE_PYTHON,
            supported_tunnel_type=Tunnel.TYPE_DNS
        )
        
        self.assertEqual(implant.supported_tunnel_type, Tunnel.TYPE_DNS)
        
        retrieved = self.implant_repo.get_implant(implant.id)
        self.assertEqual(retrieved.supported_tunnel_type, Tunnel.TYPE_DNS)

    def test_create_tunnel_linked_to_implant(self):
        """Test creating a tunnel linked to an existing implant."""
        implant = self.implants_usecase.create_implant(name="Implant1")
        
        tunnel = self.tunnels_usecase.create_tunnel(
            source_ip="10.0.0.1",
            local_port=443,
            implant_id=implant.id
        )
        
        self.assertEqual(tunnel.implant_id, implant.id)
        
        retrieved_tunnel = self.tunnel_repo.get_tunnel(tunnel.id)
        self.assertEqual(retrieved_tunnel.implant_id, implant.id)

    def test_tunnel_db_model_fields(self):
        """Verify that the DB model includes the new association fields (Logic check)."""
        from GATHERINGDB.model import TunnelDB, ImplantDB
        
        # Check TunnelDB attributes
        t_db = TunnelDB(1, "src", "dst", 80, 80, "active", "none", "phase", "HTTP", 0, 0, None, 0.0, "none", "texto plano", 99)
        self.assertEqual(t_db.implant_id, 99)
        self.assertIn("implant_id", TunnelDB.insert())
        
        # Check ImplantDB attributes
        i_db = ImplantDB(1, "name", "type", "payload", "desc", "now", "DNS")
        self.assertEqual(i_db.supported_tunnel_type, "DNS")
        self.assertIn("supported_tunnel_type", ImplantDB.insert())

if __name__ == '__main__':
    unittest.main()
