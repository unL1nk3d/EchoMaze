import unittest
from unittest.mock import MagicMock, patch
from asciimatics.screen import Screen
from UI.frames.tunnels_frame import TunnelsDashboardFrame
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.init_db import DatabaseInitializer
from tunnelsManager.adapters.drivens.RepositoryImpl import DatabaseTunnelRepository
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest
import os

class MockConnectionTester(ForConnectionTest):
    def test_local_port_open(self, port: int) -> bool:
        return True

class TestTunnelUIIntegration(unittest.TestCase):
    def setUp(self):
        self.db_file = "test_ui_int.db"
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        os.environ["GATHERINGDB_DB_PATH"] = self.db_file
        self.dao = GenericDAO()
        DatabaseInitializer.initialize_db(dao=self.dao)
        self.repo = DatabaseTunnelRepository(self.dao)
        self.tester = MockConnectionTester()
        self.usecase = TunnelsUseCase(self.repo, self.tester)
        
        self.model = MagicMock()
        self.model.tunnels = self.usecase
        self.model.cachered_ips = []
        
        self.screen = MagicMock(spec=Screen)
        self.screen.width = 80
        self.screen.height = 24
        self.screen.colours = 8
        self.screen.unicode_aware = True
        
        with patch('asciimatics.widgets.Frame.fix'):
            self.frame = TunnelsDashboardFrame(self.screen, self.model)
            self.frame._scene = MagicMock()

    def tearDown(self):
        # We need to close all connections before deleting
        from GATHERINGDB.connection import SQLiteConnectionPool
        SQLiteConnectionPool().close_all()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_add_tunnel_via_ui_logic(self):
        # Spy on the usecase and repo
        self.usecase.create_tunnel = MagicMock(side_effect=self.usecase.create_tunnel)
        self.repo.save_tunnel = MagicMock(side_effect=self.repo.save_tunnel)
        
        # Simulate filling the form
        self.frame.source_ip_text.value = "10.0.0.1"
        self.frame.local_port_text.value = "8080"
        self.frame.type_list.value = "HTTP"
        
        # Manually call the button handler
        self.frame._add_tunnel()
        
        # Check call counts
        self.assertEqual(self.usecase.create_tunnel.call_count, 1, "create_tunnel called more than once!")
        self.assertEqual(self.repo.save_tunnel.call_count, 1, "save_tunnel called more than once!")
        
        # Check database
        tunnels = self.usecase.get_all_tunnels()
        self.assertEqual(len(tunnels), 1, f"Expected 1 tunnel, found {len(tunnels)}")
        
        # Check UI list
        self.assertEqual(len(self.frame.tunnels_list.options), 1)

if __name__ == '__main__':
    unittest.main()
