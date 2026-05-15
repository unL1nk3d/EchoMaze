from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool

class ForLLMProvider(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        """Sends messages and tools to the LLM and returns the assistant message."""
        pass

class ForToolExecution(ABC):
    @abstractmethod
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Executes a tool by name with given arguments and returns the result as string."""
        pass

    @abstractmethod
    def list_tools(self) -> List[Tool]:
        """Returns a list of tools supported by this executor."""
        pass
