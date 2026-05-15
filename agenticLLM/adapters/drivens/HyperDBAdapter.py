from typing import List, Optional
import os
from datetime import datetime
from agenticLLM.models.agent import OperationalMemory
from agenticLLM.ports.drivens.forOperationalMemory import ForOperationalMemoryRepository

class HyperDBOperationalMemoryAdapter(ForOperationalMemoryRepository):
    """
    Adapter for HyperDB vector database.
    Provides semantic search capabilities for operational findings and context.
    """
    def __init__(self, db_path: str = "agent_memory.pickle.gz", embedding_function=None):
        try:
            from hyperdb import HyperDB
        except ImportError:
            raise ImportError("hyperdb-python is not installed. Please install it with 'pip install hyperdb-python'")
        
        self.db_path = db_path
        self._embedding_function = embedding_function
        self._db = None
        self._memories_cache = []
        
        # Load or initialize
        if os.path.exists(self.db_path):
            # HyperDB needs documents to initialize even when loading
            # but we can initialize empty and then load
            self._db = HyperDB([], key="content", embedding_function=self._embedding_function)
            self._db.load(self.db_path)
            # Sync internal cache
            self._memories_cache = [self._to_domain(doc) for doc in self._db.documents]
        else:
            self._db = HyperDB([], key="content", embedding_function=self._embedding_function)

    def _to_dict(self, memory: OperationalMemory) -> dict:
        return {
            "id": memory.id,
            "content": memory.content,
            "source": memory.source,
            "timestamp": memory.timestamp,
            "metadata": memory.metadata
        }

    def _to_domain(self, doc: dict) -> OperationalMemory:
        return OperationalMemory(
            id=doc.get("id"),
            content=doc.get("content"),
            source=doc.get("source"),
            timestamp=doc.get("timestamp"),
            metadata=doc.get("metadata", {})
        )

    def save_memory(self, memory: OperationalMemory) -> OperationalMemory:
        if not memory.timestamp:
            memory.timestamp = datetime.now().isoformat()
        
        if memory.id is None:
            memory.id = len(self._memories_cache) + 1
        
        doc = self._to_dict(memory)
        
        # HyperDB doesn't have an 'add' method in simple versions, 
        # it usually re-indexes the whole list.
        # We update our documents list and re-instantiate or use internal documents ref
        self._db.documents.append(doc)
        # Force re-index (HyperDB indexes on instantiation)
        self._db.instantiate_embeddings() 
        
        self._memories_cache.append(memory)
        self._db.save(self.db_path)
        return memory

    def search_memories(self, query: str, limit: int = 5) -> List[OperationalMemory]:
        if not self._db.documents:
            return []
        
        results = self._db.query(query, top_k=limit)
        return [self._to_domain(doc) for doc in results]

    def list_all_memories(self) -> List[OperationalMemory]:
        return self._memories_cache

    def clear_memories(self):
        self._db.documents = []
        self._db.instantiate_embeddings()
        self._memories_cache = []
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
