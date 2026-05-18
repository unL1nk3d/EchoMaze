from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from agenticLLM.ports.drivers.forAgentInteraction import ForAgentInteraction

class ForAgentManagement(ABC):
    @abstractmethod
    def create_agent(self, name: str, persona: str, provider: str = "mock", tools_file: Optional[str] = None) -> ForAgentInteraction:
        """Creates a new specialized agent."""
        pass

    @abstractmethod
    def get_agent(self, name: str) -> Optional[ForAgentInteraction]:
        """Retrieves an existing agent by name."""
        pass

    @abstractmethod
    def list_agents(self) -> List[str]:
        """Lists the names of all active agents."""
        pass

    @abstractmethod
    def delete_agent(self, name: str):
        """Removes an agent from the manager."""
        pass
