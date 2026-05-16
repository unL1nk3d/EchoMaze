from typing import List, Dict, Any
from agenticLLM.models.agent import Message, Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider

from agenticLLM.adapters.drivens.BaseLLMAdapter import BaseLLMAdapter

class MockLLMAdapter(BaseLLMAdapter):
    """Simple mock LLM that doesn't actually call any API but can simulate responses."""
    def __init__(self, use_react: bool = False):
        super().__init__(use_react=use_react)

    def _get_internal_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        last_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        
        if "tunnels" in last_user_msg.lower():
            return Message(role="assistant", content="I see you're asking about tunnels. You can manage them using the Tunnels Dashboard.")
        
        return Message(role="assistant", content=f"Echo: I received your message '{last_user_msg}'")
