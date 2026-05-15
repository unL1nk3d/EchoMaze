import unittest
from unittest.mock import MagicMock
import json
from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter
from agenticLLM.models.agent import OperationalMemory

class TestAgentCyberKillChain(unittest.TestCase):
    def setUp(self):
        self.tunnels_api = MagicMock()
        self.tunnels_api.list_available_functions.return_value = []
        
        self.generic_model = MagicMock()
        self.agent_usecase = MagicMock()
        self.memory_repo = MagicMock()
        self.agent_usecase.memory_repo = self.memory_repo
        self.generic_model.agent_usecase = self.agent_usecase
        
        self.adapter = SystemToolExecutorAdapter(self.tunnels_api, self.generic_model)

    def test_set_cyber_kill_chain_phase(self):
        """Test that the agent can update the kill chain phase for an IP."""
        args = {"ip": "10.0.0.5", "phase": "Exploitation"}
        result = self.adapter.execute_tool("set_cyber_kill_chain_phase", args)
        
        self.assertIn("updated to Exploitation", result)
        
        # Verify a memory was saved with the phase
        self.memory_repo.save_memory.assert_called_once()
        saved_memory = self.memory_repo.save_memory.call_args[0][0]
        self.assertEqual(saved_memory.phase, "Exploitation")
        self.assertEqual(saved_memory.metadata["target_ip"], "10.0.0.5")

    def test_get_cyber_kill_chain_status(self):
        """Test retrieving the kill chain status and history for an IP."""
        # Mock some history in the repo
        m1 = OperationalMemory(
            content="Initial phase", 
            source="kill_chain_update", 
            phase="Reconnaissance", 
            metadata={"target_ip": "10.0.0.5"},
            timestamp="2026-05-14T10:00:00"
        )
        m2 = OperationalMemory(
            content="Moving up", 
            source="kill_chain_update", 
            phase="Weaponization", 
            metadata={"target_ip": "10.0.0.5"},
            timestamp="2026-05-14T11:00:00"
        )
        self.memory_repo.list_all_memories.return_value = [m1, m2]
        
        result_json = self.adapter.execute_tool("get_cyber_kill_chain_status", {"ip": "10.0.0.5"})
        result = json.loads(result_json)
        
        self.assertEqual(result["ip"], "10.0.0.5")
        self.assertEqual(result["current_phase"], "Weaponization")
        self.assertEqual(len(result["history"]), 2)

if __name__ == '__main__':
    unittest.main()
