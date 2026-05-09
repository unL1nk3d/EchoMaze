
import unittest
import os
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB
from GATHERINGDB.model import IPNode, Artifacts
from GATHERINGDB.init_db import DatabaseInitializer
from core.scoring import ScoringEngine
from UI.models import GenericModel

class TestArtifactsScoring(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_artifacts.db"
        os.environ["GATHERINGDB_DB_PATH"] = self.db_path
        
        # Ensure any old connections are closed before deleting
        import GATHERINGDB.connection
        try:
            pool = GATHERINGDB.connection.SQLiteConnectionPool()
            pool.close_all()
        except:
            pass

        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                # Fallback if Windows still locks it
                self.db_path = "test_artifacts_alt.db"
                os.environ["GATHERINGDB_DB_PATH"] = self.db_path
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)

        GATHERINGDB.connection.SQLiteConnectionPool._DATABASE_PATH = self.db_path
        
        self.dao = GenericDAO()
        DatabaseInitializer.initialize_db(dao=self.dao)
        self.crud = CRUD_GATHERINGDB(dao=self.dao)
        self.scoring_engine = ScoringEngine(crud=self.crud)
        
        # Repository mock for GenericModel
        class MockRepo:
            def __init__(self, crud): self.crud = crud
            def select_ip_by_field(self, f, v): return self.crud.select_ip_by_field(f, v)
            def select_artifacts_by_node_id(self, nid): return self.crud.select_artifacts_by_node_id(nid)
            def insert_artifact(self, art): return self.crud.insert_artifact(art)
            def select_all_ips(self): return self.crud.select_all_ips()
            def select_all_ports(self): return self.crud.select_all_ports()

        self.model = GenericModel(
            repository=MockRepo(self.crud),
            scoring_engine=self.scoring_engine
        )
        
        # Insert a node
        self.ip = "10.0.0.1"
        self.crud.insert_ip(self.ip, "/tmp", "", 0)
        self.model.selected_ip = self.ip

    def tearDown(self):
        import GATHERINGDB.connection
        pool = GATHERINGDB.connection.SQLiteConnectionPool()
        pool.close_all()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_add_artifact_increases_score(self):
        initial_score = self.scoring_engine.get_score(self.ip)
        self.assertEqual(initial_score, 0.0)
        
        # Add a "mimikatz" artifact which should have a high default score
        success = self.model.add_artifact(self.ip, "mimikatz.exe", "Credential dumping")
        self.assertTrue(success)
        
        new_score = self.scoring_engine.get_score(self.ip)
        # Default for mimikatz is 50.0
        # For opsec_flag=0 (default), mod is 1.0
        # 50.0 * 1.0 = 50.0
        self.assertEqual(new_score, 50.0)
        
        # Check if artifact is in DB
        artifacts = self.model.get_artifacts_for_ip(self.ip)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].filename, "mimikatz.exe")

    def test_add_custom_score_artifact(self):
        initial_score = self.scoring_engine.get_score(self.ip)
        
        # Add artifact with custom score
        self.model.add_artifact(self.ip, "harmless.txt", "Just a note", noise_score=1.0)
        
        new_score = self.scoring_engine.get_score(self.ip)
        # 1.0 * 1.0 (mod for flag 0) = 1.0
        self.assertEqual(new_score, 1.0)

if __name__ == "__main__":
    unittest.main()
