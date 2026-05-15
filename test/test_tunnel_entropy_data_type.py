import unittest
from tunnelsManager.models.tunnel import Tunnel
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.adapters.drivens.RepositoryImpl import InMemoryTunnelRepository
from tunnelsManager.adapters.drivens.ConnectionTestImpl import NetworkConnectionTester
import core.entropy as entropy

class TestTunnelEntropyDataType(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryTunnelRepository()
        self.connection_tester = NetworkConnectionTester()
        self.usecase = TunnelsUseCase(self.repository, self.connection_tester)

    def test_evaluate_entropy_with_predefined_data_type(self):
        # Create a tunnel with a specific data type (e.g., 'imagenes jpeg')
        # even if the tunnel_type is HTTP (usually 'texto plano')
        tunnel = self.usecase.create_tunnel(
            source_ip="192.168.1.1", 
            local_port=80, 
            tunnel_type=Tunnel.TYPE_HTTP, 
            data_type="imagenes jpeg"
        )
        
        # Add some data transfer so it can hide 1KB
        self.usecase.register_data_transfer(tunnel.id, 2048, 2048)
        
        self.usecase.evaluate_tunnel_entropy(tunnel.id)
        
        updated_tunnel = self.repository.get_tunnel(tunnel.id)
        
        # The entropy score for 'imagenes jpeg' is 7.6
        self.assertEqual(updated_tunnel.entropy_score, 7.6)
        self.assertIn("imagenes jpeg", updated_tunnel.entropy_warning)

    def test_evaluate_entropy_fallback_mapping(self):
        # Create a tunnel with default data type
        tunnel = self.usecase.create_tunnel(
            source_ip="192.168.1.1", 
            local_port=443, 
            tunnel_type=Tunnel.TYPE_SHADOWSOCKS
        )
        
        self.usecase.register_data_transfer(tunnel.id, 2048, 2048)
        self.usecase.evaluate_tunnel_entropy(tunnel.id)
        
        updated_tunnel = self.repository.get_tunnel(tunnel.id)
        
        # Shadowsocks defaults to 'datos cifrados' (8.9)
        self.assertEqual(updated_tunnel.entropy_score, 8.9)
        self.assertIn("datos cifrados", updated_tunnel.entropy_warning)

if __name__ == '__main__':
    unittest.main()
