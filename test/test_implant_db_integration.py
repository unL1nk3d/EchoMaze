import unittest
from unittest.mock import MagicMock
from tunnelsManager.adapters.drivens.RepositoryImpl import DatabaseImplantRepository
from tunnelsManager.models.implant import Implant
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.init_db import DatabaseInitializer
import os

class TestImplantDBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_implants.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        
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
        self.repo = DatabaseImplantRepository(self.dao)

    def test_save_and_retrieve_implant(self):
        implant = Implant(
            name="Reverse Shell",
            implant_type=Implant.TYPE_PYTHON,
            payload="import socket...",
            description="Basic python revshell"
        )
        
        saved = self.repo.save_implant(implant)
        self.assertIsNotNone(saved.id)
        
        retrieved = self.repo.get_implant(saved.id)
        self.assertEqual(retrieved.name, "Reverse Shell")
        self.assertEqual(retrieved.implant_type, Implant.TYPE_PYTHON)

if __name__ == '__main__':
    unittest.main()
