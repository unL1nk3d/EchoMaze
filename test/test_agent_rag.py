import unittest
from agenticLLM.models.agent import OperationalMemory, Message
from agenticLLM.core.agent_use_case import AgentUseCase
from agenticLLM.adapters.drivens.OperationalMemoryAdapter import InMemoryOperationalMemoryAdapter
from unittest.mock import MagicMock

class TestAgentRAG(unittest.TestCase):
    def setUp(self):
        self.memory_repo = InMemoryOperationalMemoryAdapter()
        self.llm = MagicMock()
        self.tools = MagicMock()
        self.tools.list_tools.return_value = []
        self.use_case = AgentUseCase(self.llm, self.tools, self.memory_repo)

    def test_memory_retrieval_and_injection(self):
        """Test that relevant memories are injected into the agent's context."""
        # 1. Save a relevant memory
        self.memory_repo.save_memory(OperationalMemory(
            content="The target 10.0.0.5 has a weak password on SSH: 'admin123'",
            source="user_note"
        ))
        
        # 2. Ask a question related to that memory
        self.llm.generate_response.return_value = Message(role="assistant", content="Acknowledged.")
        
        self.use_case.ask("What do we know about 10.0.0.5?")
        
        # 3. Verify that the RAG message was sent to the LLM
        # The first message is system, the second should be the user message with context
        history = self.use_case.get_history()
        user_msg = history[1]
        
        self.assertEqual(user_msg.role, "user")
        self.assertIn("Relevant operational context found", user_msg.content)
        self.assertIn("admin123", user_msg.content)
        self.assertIn("10.0.0.5", user_msg.content)

    def test_memory_storage_via_tool(self):
        """Test that the agent can save findings via its tool adapter (Logic check)."""
        from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter
        
        generic_model = MagicMock()
        generic_model.agent_usecase = self.use_case
        
        adapter = SystemToolExecutorAdapter(MagicMock(), generic_model)
        
        # Execute tool to add memory
        adapter.execute_tool("add_to_operational_memory", {"content": "Found active EDR on 192.168.1.10"})
        
        # Verify it's in the repo
        memories = self.memory_repo.list_all_memories()
        self.assertEqual(len(memories), 1)
        self.assertIn("EDR", memories[0].content)

if __name__ == '__main__':
    unittest.main()
