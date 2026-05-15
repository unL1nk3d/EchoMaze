import unittest
from tunnelsManager.models.tunnel import Tunnel
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.adapters.drivens.RepositoryImpl import InMemoryTunnelRepository
from tunnelsManager.adapters.drivens.ConnectionTestImpl import NetworkConnectionTester

class TestSocks4Tunnel(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryTunnelRepository()
        self.connection_tester = NetworkConnectionTester()
        self.usecase = TunnelsUseCase(self.repository, self.connection_tester)

    def test_create_socks4_tunnel(self):
        tunnel = self.usecase.create_tunnel(
            source_ip="10.0.0.1",
            local_port=1080,
            tunnel_type=Tunnel.TYPE_SOCKS4
        )
        self.assertEqual(tunnel.tunnel_type, Tunnel.TYPE_SOCKS4)
        self.assertEqual(tunnel.local_port, 1080)

    def test_socks4_entropy_evaluation(self):
        tunnel = self.usecase.create_tunnel(
            source_ip="10.0.0.1",
            local_port=1080,
            tunnel_type=Tunnel.TYPE_SOCKS4
        )
        
        # Register some data
        self.usecase.register_data_transfer(tunnel.id, 1024, 1024)
        
        # Evaluate entropy
        self.usecase.evaluate_tunnel_entropy(tunnel.id)
        
        updated_tunnel = self.repository.get_tunnel(tunnel.id)
        
        # SOCKS4 should map to 'datos cifrados' (8.9)
        self.assertEqual(updated_tunnel.entropy_score, 8.9)
        self.assertIn("datos cifrados", updated_tunnel.entropy_warning)
        self.assertIn(Tunnel.TYPE_SOCKS4, updated_tunnel.entropy_warning)

if __name__ == '__main__':
    unittest.main()
