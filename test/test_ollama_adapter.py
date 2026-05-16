import unittest
from unittest.mock import patch, MagicMock
import json
from agenticLLM.adapters.drivens.OllamaAdapter import OllamaAdapter
from agenticLLM.models.agent import Message, Tool

class TestOllamaAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = OllamaAdapter(model_name="test-model", base_url="http://test-ollama:11434")

    @patch('urllib.request.urlopen')
    def test_generate_response_simple(self, mock_urlopen):
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "role": "assistant",
                "content": "Hello! I am ready to help."
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        messages = [Message(role="user", content="Hi")]
        response = self.adapter.generate_response(messages, [])

        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.content, "Hello! I am ready to help.")
        self.assertIsNone(response.tool_call_id)

    @patch('urllib.request.urlopen')
    def test_generate_response_with_tool_call(self, mock_urlopen):
        # Mock response with tool call
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_weather",
                            "arguments": {"location": "London"}
                        }
                    }
                ]
            }
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        messages = [Message(role="user", content="What's the weather in London?")]
        tools = [Tool(name="get_weather", description="Get weather", parameters={"type": "object", "properties": {"location": {"type": "string"}}})]
        
        response = self.adapter.generate_response(messages, tools)

        self.assertEqual(response.role, "assistant")
        self.assertEqual(json.loads(response.content), {"location": "London"})
        self.assertEqual(response.tool_call_id, "ollama_get_weather")
        self.assertEqual(response.name, "get_weather")

    @patch('urllib.request.urlopen')
    def test_generate_response_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection failed")

        messages = [Message(role="user", content="Hi")]
        response = self.adapter.generate_response(messages, [])

        self.assertIn("Unexpected error calling Ollama", response.content)

if __name__ == '__main__':
    unittest.main()
