from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message

class ForAgentInteraction(ABC):
    @abstractmethod
    def ask(self, user_input: str) -> str:
        """Processes user input and returns the agent's response."""
        pass

    @abstractmethod
    def get_history(self) -> List[Message]:
        """Returns the conversation history."""
        pass

    @abstractmethod
    def reset(self):
        """Clears the agent state."""
        pass

    @abstractmethod
    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        """Returns the current pending action requiring approval."""
        pass

    @abstractmethod
    def provide_approval(self, approved: bool) -> str:
        """Resumes agent execution after operator approval/rejection."""
        pass

    @abstractmethod
    def get_tools_json(self) -> str:
        """Returns the available tools in JSON format."""
        pass

    @abstractmethod
    def get_trace(self) -> List[Dict[str, Any]]:
        """Returns the execution trace for debugging."""
        pass
