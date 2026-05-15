import unittest
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.init_db import DatabaseInitializer
from tunnelsManager.adapters.drivens.RepositoryImpl import DatabaseTunnelRepository
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.ports.drivens.forConnectionTest import ForConnectionTest
import os

class MockConnectionTester(ForConnectionTest):
    def test_local_port_open(self, port: int) -> bool:
        return True

class TestTunnelDuplication(unittest.TestCase):
    def setUp(self):
        self.db_file = "test_duplication.db"
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        os.environ["GATHERINGDB_DB_PATH"] = self.db_file
        self.dao = GenericDAO()
        DatabaseInitializer.initialize_db(dao=self.dao)
        self.repo = DatabaseTunnelRepository(self.dao)
        self.tester = MockConnectionTester()
        self.usecase = TunnelsUseCase(self.repo, self.tester)

    def tearDown(self):
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_create_tunnel_no_duplicates(self):
        # Create one tunnel
        self.usecase.create_tunnel("127.0.0.1", 8080)
        
        # Check all tunnels
        tunnels = self.usecase.get_all_tunnels()
        self.assertEqual(len(tunnels), 1, f"Expected 1 tunnel, found {len(tunnels)}")

if __name__ == '__main__':
    unittest.main()
