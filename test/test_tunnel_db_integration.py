import unittest
from unittest.mock import MagicMock
from tunnelsManager.adapters.drivens.RepositoryImpl import DatabaseTunnelRepository
from tunnelsManager.models.tunnel import Tunnel
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.init_db import DatabaseInitializer
import os

class TestTunnelDBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a temporary test database
        cls.db_path = "test_tunnels.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        
        # Configure environment for GATHERINGDB
        os.environ["GATHERINGDB_DB_PATH"] = cls.db_path
        os.environ["GATHERINGDB_POOL_SIZE"] = "2"
        
        cls.dao = GenericDAO()
        DatabaseInitializer.initialize_db(dao=cls.dao)

    @classmethod
    def tearDownClass(cls):
        from GATHERINGDB.connection import SQLiteConnectionPool
        pool = SQLiteConnectionPool()
        pool.close_all()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.repo = DatabaseTunnelRepository(self.dao)

    def test_save_and_retrieve_tunnel(self):
        tunnel = Tunnel(
            source_ip="192.168.1.100",
            local_port=4444,
            tunnel_type=Tunnel.TYPE_SHADOWSOCKS,
            phase=Tunnel.PHASE_READY_TO_SEND,
            status=Tunnel.STATUS_ACTIVE
        )
        
        # Save
        saved_tunnel = self.repo.save_tunnel(tunnel)
        self.assertIsNotNone(saved_tunnel.id)
        
        # Retrieve
        retrieved = self.repo.get_tunnel(saved_tunnel.id)
        self.assertEqual(retrieved.source_ip, "192.168.1.100")
        self.assertEqual(retrieved.tunnel_type, Tunnel.TYPE_SHADOWSOCKS)
        self.assertEqual(retrieved.phase, Tunnel.PHASE_READY_TO_SEND)

    def test_list_tunnels(self):
        t1 = Tunnel(source_ip="1.1.1.1", local_port=1111)
        t2 = Tunnel(source_ip="2.2.2.2", local_port=2222)
        
        self.repo.save_tunnel(t1)
        self.repo.save_tunnel(t2)
        
        tunnels = self.repo.list_tunnels()
        ips = [t.source_ip for t in tunnels]
        self.assertIn("1.1.1.1", ips)
        self.assertIn("2.2.2.2", ips)

    def test_delete_tunnel(self):
        t = Tunnel(source_ip="delete.me", local_port=9999)
        saved = self.repo.save_tunnel(t)
        
        self.repo.delete_tunnel(saved.id)
        self.assertIsNone(self.repo.get_tunnel(saved.id))

if __name__ == '__main__':
    unittest.main()
