import unittest
from unittest.mock import MagicMock
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.models.tunnel import Tunnel

class TestTunnelPhases(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.connection_tester = MagicMock()
        self.use_case = TunnelsUseCase(self.repository, self.connection_tester)

    def test_create_tunnel_starts_in_creation_phase(self):
        self.repository.save_tunnel.side_effect = lambda x: x
        tunnel = self.use_case.create_tunnel("1.1.1.1", 8080)
        self.assertEqual(tunnel.phase, Tunnel.PHASE_CREATION)
        self.assertEqual(tunnel.tunnel_type, Tunnel.TYPE_HTTP) # Default

    def test_create_tunnel_with_specific_type(self):
        self.repository.save_tunnel.side_effect = lambda x: x
        tunnel = self.use_case.create_tunnel("1.1.1.1", 8080, tunnel_type=Tunnel.TYPE_SOCKS4)
        self.assertEqual(tunnel.tunnel_type, Tunnel.TYPE_SOCKS4)

    def test_advance_tunnel_phases(self):
        tunnel = Tunnel(id=1, source_ip="1.1.1.1", local_port=8080, phase=Tunnel.PHASE_CREATION)
        self.repository.get_tunnel.return_value = tunnel
        self.repository.save_tunnel.side_effect = lambda x: x

        # Creation -> Setting Up (via advance or explicit call)
        updated_tunnel = self.use_case.setup_tunnel(1)
        self.assertEqual(updated_tunnel.phase, Tunnel.PHASE_SETTING_UP)

        # Setting Up -> Interface Registration
        updated_tunnel = self.use_case.register_interface(1)
        self.assertEqual(updated_tunnel.phase, Tunnel.PHASE_INTERFACE_REGISTRATION)

        # Interface Registration -> Ready to Send
        updated_tunnel = self.use_case.set_ready(1)
        self.assertEqual(updated_tunnel.phase, Tunnel.PHASE_READY_TO_SEND)
        self.assertEqual(updated_tunnel.status, Tunnel.STATUS_ACTIVE)

    def test_explicit_methods_adhere_to_sequence(self):
        tunnel = Tunnel(id=1, source_ip="1.1.1.1", local_port=8080, phase=Tunnel.PHASE_CREATION)
        self.repository.get_tunnel.return_value = tunnel
        self.repository.save_tunnel.side_effect = lambda x: x

        # Cannot skip to Interface Registration from Creation
        updated_tunnel = self.use_case.register_interface(1)
        self.assertEqual(updated_tunnel.phase, Tunnel.PHASE_CREATION)

        # Cannot skip to Ready to Send from Creation
        updated_tunnel = self.use_case.set_ready(1)
        self.assertEqual(updated_tunnel.phase, Tunnel.PHASE_CREATION)

    def test_data_metrics_registration(self):
        tunnel = Tunnel(id=1, source_ip="1.1.1.1", local_port=8080)
        self.repository.get_tunnel.return_value = tunnel
        self.repository.save_tunnel.side_effect = lambda x: x

        self.use_case.register_data_transfer(1, 100, 200)
        
        self.assertEqual(tunnel.data_sent_bytes, 100)
        self.assertEqual(tunnel.data_received_bytes, 200)
        self.assertIsNotNone(tunnel.last_activity)

        metrics = self.use_case.get_tunnel_metrics(1)
        self.assertEqual(metrics["sent_bytes"], 100)
        self.assertEqual(metrics["received_bytes"], 200)

    def test_entropy_evaluation(self):
        tunnel = Tunnel(id=1, source_ip="1.1.1.1", local_port=8080, tunnel_type=Tunnel.TYPE_IMAGE_TUNNEL, data_sent_bytes=5000)
        self.repository.get_tunnel.return_value = tunnel
        self.repository.save_tunnel.side_effect = lambda x: x
        self.repository.list_tunnels.return_value = [tunnel]

        # Evaluate individual entropy
        self.use_case.evaluate_tunnel_entropy(1)
        
        self.assertEqual(tunnel.entropy_score, 7.6) # entropy.ENTROPY_DATA_TYPES['imagenes jpeg']
        self.assertIn("Camuflaje válido", tunnel.entropy_warning)

        # Evaluate global entropy stats
        stats = self.use_case.get_tunnel_stats()
        self.assertEqual(stats["global_entropy"], 0.0) # Only one type, entropy is 0
        self.assertIn("Baja entropía", stats["entropy_warning"])

if __name__ == '__main__':
    unittest.main()
