from typing import List
from agenticLLM.models.agent import OperationalMemory
from agenticLLM.ports.drivens.forOperationalMemory import ForOperationalMemoryRepository
from datetime import datetime

class InMemoryOperationalMemoryAdapter(ForOperationalMemoryRepository):
    """
    Simplified in-memory RAG implementation.
    In a real scenario, this would use vector embeddings and a vector DB.
    For now, it uses simple keyword matching to simulate RAG retrieval.
    """
    def __init__(self):
        self._memories: List[OperationalMemory] = []
        self._counter = 1

    def save_memory(self, memory: OperationalMemory) -> OperationalMemory:
        if memory.id is None:
            memory.id = self._counter
            self._counter += 1
        if not memory.timestamp:
            memory.timestamp = datetime.now().isoformat()
        self._memories.append(memory)
        return memory

    def search_memories(self, query: str, limit: int = 5) -> List[OperationalMemory]:
        # Simple RAG simulation: keyword matching
        keywords = query.lower().split()
        scored_memories = []
        
        for m in self._memories:
            score = 0
            content_lower = m.content.lower()
            for kw in keywords:
                if kw in content_lower:
                    score += 1
            if score > 0:
                scored_memories.append((score, m))
        
        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [m for score, m in scored_memories[:limit]]

    def list_all_memories(self) -> List[OperationalMemory]:
        return self._memories

    def clear_memories(self):
        self._memories = []
