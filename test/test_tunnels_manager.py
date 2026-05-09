import unittest
from unittest.mock import MagicMock
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.models.tunnel import Tunnel

class TestTunnelsManager(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.connection_tester = MagicMock()
        self.use_case = TunnelsUseCase(self.repository, self.connection_tester)

    def test_set_check_policy(self):
        self.use_case.set_connection_check_policy(30)
        self.assertEqual(self.use_case.check_interval, 30)

    def test_check_tunnels_health_updates_status(self):
        # Setup tunnels
        t1 = Tunnel(id=1, source_ip="1.1.1.1", dest_ip="2.2.2.2", local_port=80, remote_port=80, status=Tunnel.STATUS_ACTIVE)
        t2 = Tunnel(id=2, source_ip="1.1.1.1", dest_ip="3.3.3.3", local_port=443, remote_port=443, status=Tunnel.STATUS_DISCONNECTED)
        t3 = Tunnel(id=3, source_ip="1.1.1.1", dest_ip="4.4.4.4", local_port=22, remote_port=22, status=Tunnel.STATUS_DEACTIVATED)
        
        self.repository.list_tunnels.return_value = [t1, t2, t3]
        
        # Connection tester behavior
        # t1: active -> disconnected (port closed)
        # t2: disconnected -> active (port opened)
        # t3: deactivated -> stays deactivated (not checked)
        self.connection_tester.test_local_port_open.side_effect = lambda port: {80: False, 443: True}[port]
        
        self.use_case.check_tunnels_health()
        
        self.assertEqual(t1.status, Tunnel.STATUS_DISCONNECTED)
        self.assertEqual(t2.status, Tunnel.STATUS_ACTIVE)
        self.assertEqual(t3.status, Tunnel.STATUS_DEACTIVATED)
        
        # Verify save_tunnel was called for t1 and t2
        self.assertEqual(self.repository.save_tunnel.call_count, 2)

    def test_get_tunnel_stats_detailed(self):
        t1 = Tunnel(id=1, source_ip="1.1.1.1", dest_ip="2.2.2.2", local_port=80, remote_port=80, status=Tunnel.STATUS_ACTIVE)
        t2 = Tunnel(id=2, source_ip="1.1.1.1", dest_ip="3.3.3.3", local_port=443, remote_port=443, status=Tunnel.STATUS_ACTIVATING)
        t3 = Tunnel(id=3, source_ip="1.1.1.1", dest_ip=None, local_port=22, remote_port=22, status=Tunnel.STATUS_FILTERED)
        
        self.repository.list_tunnels.return_value = [t1, t2, t3]
        
        stats = self.use_case.get_tunnel_stats()
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['active'], 1)
        self.assertEqual(stats['activating'], 1)
        self.assertEqual(stats['filtered'], 1)
        self.assertEqual(stats['hanging'], 1)

    def test_activate_deactivate_tunnel(self):
        t1 = Tunnel(id=1, source_ip="1.1.1.1", dest_ip="2.2.2.2", local_port=80, remote_port=80, status=Tunnel.STATUS_DISCONNECTED)
        self.repository.list_tunnels.return_value = [t1]
        
        # Test activate
        self.use_case.activate_tunnel(1)
        self.assertEqual(t1.status, Tunnel.STATUS_ACTIVE)
        
        # Test deactivate
        self.use_case.deactivate_tunnel(1)
        self.assertEqual(t1.status, Tunnel.STATUS_DEACTIVATED)

    def test_implant_beaconing_logic(self):
        t1 = Tunnel(id=1, source_ip="1.1.1.1", dest_ip="2.2.2.2", local_port=80, remote_port=80, status=Tunnel.STATUS_ACTIVATING, technique=Tunnel.TECHNIQUE_BEACONING)
        self.repository.list_tunnels.return_value = [t1]
        
        # 1. Receive beacon while activating -> active
        self.use_case.process_implant_beacon(1)
        self.assertEqual(t1.status, Tunnel.STATUS_ACTIVE)
        
        # 2. Deactivate tunnel
        self.use_case.deactivate_tunnel(1)
        self.assertEqual(t1.status, Tunnel.STATUS_DEACTIVATED)
        
        # 3. Receive beacon while deactivated -> stays deactivated
        self.use_case.process_implant_beacon(1)
        self.assertEqual(t1.status, Tunnel.STATUS_DEACTIVATED)

if __name__ == '__main__':
    unittest.main()
