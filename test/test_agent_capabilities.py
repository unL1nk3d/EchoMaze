import unittest
from unittest.mock import MagicMock
from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter

class TestAgentCapabilities(unittest.TestCase):
    def setUp(self):
        self.tunnels_api = MagicMock()
        self.tunnels_api.list_available_functions.return_value = [
            {"name": "get_all_tunnels", "description": "Lists tunnels", "signature": "()"}
        ]
        
        self.generic_model = MagicMock()
        # Mock cachered_ips
        self.generic_model.cachered_ips = [("192.168.1.1", "", ["http"], 0)]
        # Mock get_opsec_data
        self.generic_model.get_opsec_data.return_value = {"noise_score": 10, "risk_color": "green"}
        # Mock artifacts
        artifact = MagicMock()
        artifact.filename = "exploit.exe"
        self.generic_model.get_artifacts_for_ip.return_value = [artifact]

        self.adapter = SystemToolExecutorAdapter(self.tunnels_api, self.generic_model)

    def test_list_tools_includes_new_capabilities(self):
        tools = self.adapter.list_tools()
        tool_names = [t.name for t in tools]
        
        self.assertIn("tunnels_get_all_tunnels", tool_names)
        self.assertIn("get_network_topology", tool_names)
        self.assertIn("get_ip_opsec_analysis", tool_names)
        self.assertIn("get_artifacts", tool_names)

    def test_execute_get_network_topology(self):
        result = self.adapter.execute_tool("get_network_topology", {})
        self.assertIn("192.168.1.1", result)
        self.assertIn("http", result)

    def test_execute_get_ip_opsec_analysis(self):
        result = self.adapter.execute_tool("get_ip_opsec_analysis", {"ip": "192.168.1.1"})
        self.assertIn("noise_score", result)
        self.assertIn("10", result)

    def test_execute_get_artifacts(self):
        # We need vars() to work on the mock artifact or use a real object/dict
        # In the adapter we use [vars(a) for a in artifacts]
        from dataclasses import dataclass
        @dataclass
        class MockArtifact:
            filename: str
        
        self.generic_model.get_artifacts_for_ip.return_value = [MockArtifact("exploit.exe")]
        
        result = self.adapter.execute_tool("get_artifacts", {"ip": "192.168.1.1"})
        self.assertIn("exploit.exe", result)

    def test_execute_search_techniques(self):
        # Mock Ingestor result
        from dataclasses import dataclass
        @dataclass
        class MockTemplate:
            name: str
            technique: str
        
        mock_result = MagicMock()
        mock_result.templates = [MockTemplate("SSH Bruteforce", "T1110")]
        self.generic_model.ingestor.searchCoincidence.return_value = mock_result
        
        result = self.adapter.execute_tool("search_techniques", {"query": "ssh"})
        self.assertIn("SSH Bruteforce", result)
        self.assertIn("T1110", result)

if __name__ == '__main__':
    unittest.main()
