from abc import ABC, abstractmethod
from typing import List, Dict, Any
from agenticLLM.models.agent import Skill

class ForSkillRegistry(ABC):
    @abstractmethod
    def register_skill(self, skill: Skill, callback: callable):
        """Registers a new skill with its execution callback."""
        pass

    @abstractmethod
    def list_available_skills(self) -> List[Skill]:
        """Returns all registered skills."""
        pass

    @abstractmethod
    def execute_skill(self, name: str, params: Dict[str, Any]) -> str:
        """Finds and executes a skill by name."""
        pass
