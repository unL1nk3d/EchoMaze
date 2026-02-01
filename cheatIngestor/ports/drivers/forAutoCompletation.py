from abc import ABC, abstractmethod
from cheatIngestor.models.template import Technique

class ForAutoComplete(ABC):
    @abstractmethod
    def searchCoincidence(self, keyword: str) -> Technique:
        ...