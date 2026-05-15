from abc import ABC, abstractmethod
from typing import List, Optional
from agenticLLM.models.agent import OperationalMemory

class ForOperationalMemoryRepository(ABC):
    @abstractmethod
    def save_memory(self, memory: OperationalMemory) -> OperationalMemory:
        """Persists an operational memory entry."""
        pass

    @abstractmethod
    def search_memories(self, query: str, limit: int = 5) -> List[OperationalMemory]:
        """Retrieves memories relevant to the query (RAG-like)."""
        pass

    @abstractmethod
    def list_all_memories(self) -> List[OperationalMemory]:
        """Lists all stored operational memories."""
        pass

    @abstractmethod
    def clear_memories(self):
        """Removes all stored memories."""
        pass
