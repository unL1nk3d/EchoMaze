import unittest
from unittest.mock import MagicMock
from agenticLLM.core.agent_use_case import AgentUseCase
from agenticLLM.models.agent import Message, Tool, Skill

class TestAgentHITL(unittest.TestCase):
    def setUp(self):
        self.llm = MagicMock()
        self.tools = MagicMock()
        self.memory = MagicMock()
        self.skills = MagicMock()
        
        # Define a tool that requires approval
        self.sensitive_tool = Tool(name="run_shell", description="desc", parameters={}, requires_approval=True)
        self.tools.list_tools.return_value = [self.sensitive_tool]
        
        self.use_case = AgentUseCase(self.llm, self.tools, self.memory, self.skills)

    def test_approval_flow_interrupts_execution(self):
        """Test that execution pauses when a sensitive tool is called."""
        # LLM decides to call run_shell
        self.llm.generate_response.return_value = Message(
            role="assistant", 
            content='{"cmd": "whoami"}', 
            tool_call_id="call_1", 
            name="run_shell"
        )
        
        response = self.use_case.ask("Execute whoami")
        
        # Verify execution is paused
        self.assertIn("[WAITING_FOR_APPROVAL]", response)
        self.assertIsNotNone(self.use_case.get_pending_action())
        self.assertEqual(self.use_case.get_pending_action()['tool_name'], "run_shell")
        
        # Verify tool was NOT executed yet
        self.tools.execute_tool.assert_not_called()

    def test_approval_flow_resumes_on_approve(self):
        """Test that execution resumes and tool is called after approval."""
        self.llm.generate_response.side_effect = [
            Message(role="assistant", content='{"cmd": "whoami"}', tool_call_id="call_1", name="run_shell"),
            Message(role="assistant", content="The user is root.")
        ]
        self.tools.execute_tool.return_value = "root"
        
        self.use_case.ask("Execute whoami")
        
        # Provide approval
        final_response = self.use_case.provide_approval(True)
        
        # Verify tool WAS executed
        self.tools.execute_tool.assert_called_with("run_shell", {"cmd": "whoami"})
        self.assertEqual(final_response, "The user is root.")

    def test_approval_flow_aborts_on_reject(self):
        """Test that execution resumes with rejection message if operator says no."""
        self.llm.generate_response.side_effect = [
            Message(role="assistant", content='{"cmd": "whoami"}', tool_call_id="call_1", name="run_shell"),
            Message(role="assistant", content="I cannot proceed without your permission.")
        ]
        
        self.use_case.ask("Execute whoami")
        
        # Provide rejection
        final_response = self.use_case.provide_approval(False)
        
        # Verify tool was NOT executed
        self.tools.execute_tool.assert_not_called()
        self.assertEqual(final_response, "I cannot proceed without your permission.")
        
        # Check history to see if rejection was recorded
        history = self.use_case.get_history()
        # History: System, User, Assistant (call), Tool (rejection), Assistant (final)
        self.assertIn("rejected by operator", history[3].content)

if __name__ == '__main__':
    unittest.main()
