import unittest
from unittest.mock import MagicMock
from agenticLLM.core.agent_use_case import AgentUseCase
from agenticLLM.models.agent import Message, Tool, AgentConfig

class TestAgentTracing(unittest.TestCase):
    def setUp(self):
        self.llm = MagicMock()
        self.tools = MagicMock()
        self.memory = MagicMock()
        self.skills = MagicMock()
        self.tools.list_tools.return_value = []
        self.memory.search_memories.return_value = []
        
        self.agent = AgentUseCase(
            llm=self.llm,
            tools=self.tools,
            memory_repo=self.memory,
            skills=self.skills,
            agent_name="test_agent"
        )

    def test_tracing_reasoning_and_complete(self):
        # Mock LLM to return a direct answer
        self.llm.generate_response.return_value = Message(role="assistant", content="Hello!")
        
        self.agent.ask("Hi")
        
        trace = self.agent.get_trace()
        self.assertTrue(any(s['stage'] == 'REASONING' and 'Hello!' in s['content'] for s in trace))
        self.assertTrue(any(s['stage'] == 'COMPLETE' for s in trace))

    def test_tracing_tool_call(self):
        # 1. LLM returns tool call
        self.llm.generate_response.side_effect = [
            Message(role="assistant", content="Testing tool", tool_call_id="call_1", name="test_tool"),
            Message(role="assistant", content="Done!")
        ]
        self.tools.execute_tool.return_value = "Tool Result"
        
        self.agent.ask("Run tool")
        
        trace = self.agent.get_trace()
        self.assertTrue(any(s['stage'] == 'TOOL_CALL' and 'test_tool' in s['content'] for s in trace))
        self.assertTrue(any(s['stage'] == 'OBSERVATION' and 'Tool Result' in s['content'] for s in trace))

    def test_tracing_delegation(self):
        # Mock delegation
        self.llm.generate_response.side_effect = [
            Message(role="assistant", content="Delegating", tool_call_id="call_2", name="delegate_to_agent"),
            Message(role="assistant", content="Task finished")
        ]
        self.tools.execute_tool.return_value = "Success from delegated agent"
        
        self.agent.ask("Delegate task")
        
        trace = self.agent.get_trace()
        self.assertTrue(any(s['stage'] == 'DELEGATION' for s in trace))
        self.assertTrue(any(s['stage'] == 'OBSERVATION' and 'Success from delegated agent' in s['content'] for s in trace))

if __name__ == "__main__":
    unittest.main()
