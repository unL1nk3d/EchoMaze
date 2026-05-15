import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock the entire hyperdb module before any imports from our code
mock_hyperdb_module = MagicMock()
sys.modules['hyperdb'] = mock_hyperdb_module

from agenticLLM.models.agent import OperationalMemory
from agenticLLM.adapters.drivens.HyperDBAdapter import HyperDBOperationalMemoryAdapter

class TestHyperDBAdapter(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_memory.pickle.gz"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.mock_db_instance = MagicMock()
        mock_hyperdb_module.HyperDB.return_value = self.mock_db_instance
        
        # Initial documents list
        self.mock_db_instance.documents = []

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_sync(self):
        adapter = HyperDBOperationalMemoryAdapter(db_path=self.db_path)
        
        memory = OperationalMemory(content="Target 10.0.0.1 is vulnerable to MS17-010", source="agent")
        adapter.save_memory(memory)
        
        # Verify it was added to HyperDB documents
        self.assertEqual(len(self.mock_db_instance.documents), 1)
        self.assertEqual(self.mock_db_instance.documents[0]['content'], memory.content)
        
        # Verify save was called
        self.mock_db_instance.save.assert_called_with(self.db_path)
        # Verify re-indexing
        self.mock_db_instance.instantiate_embeddings.assert_called()

    def test_search_delegation(self):
        self.mock_db_instance.documents = [{"content": "found creds", "id": 1}]
        self.mock_db_instance.query.return_value = [{"content": "found creds", "id": 1}]
        
        adapter = HyperDBOperationalMemoryAdapter(db_path=self.db_path)
        results = adapter.search_memories("creds")
        
        self.mock_db_instance.query.assert_called_with("creds", top_k=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "found creds")

if __name__ == '__main__':
    unittest.main()
