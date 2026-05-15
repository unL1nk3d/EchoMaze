import unittest
from unittest.mock import MagicMock
from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter

class TestAgentLogging(unittest.TestCase):
    def setUp(self):
        self.tunnels_api = MagicMock()
        self.tunnels_api.list_available_functions.return_value = []
        
        self.generic_model = MagicMock()
        self.adapter = SystemToolExecutorAdapter(self.tunnels_api, self.generic_model)

    def test_execute_register_action(self):
        """Test that agent can register actions through the adapter."""
        self.generic_model.add_action.return_value = True
        
        args = {
            "ip": "10.0.0.1",
            "command": "cat /etc/passwd",
            "noise_score": 15.5
        }
        result = self.adapter.execute_tool("register_action", args)
        
        self.assertIn("registered and scored", result)
        self.generic_model.add_action.assert_called_with(
            "10.0.0.1", "EchoAI_Agent", "cat /etc/passwd", 15.5
        )

    def test_execute_register_artifact(self):
        """Test that agent can register artifacts through the adapter."""
        self.generic_model.add_artifact.return_value = True
        
        args = {
            "ip": "10.0.0.2",
            "filename": "shadow.bak",
            "notes": "exfiltrated shadow file",
            "noise_score": 50.0
        }
        result = self.adapter.execute_tool("register_artifact", args)
        
        self.assertIn("registered and scored", result)
        self.generic_model.add_artifact.assert_called_with(
            "10.0.0.2", "shadow.bak", "exfiltrated shadow file", 50.0
        )

if __name__ == '__main__':
    unittest.main()
