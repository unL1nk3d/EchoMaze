from abc import ABC,abstractmethod
from cheatIngestor.models.template import Technique
class ForDocumentIngestion(ABC):
    @abstractmethod
    def ingestJsonDocument(self,document:str) -> Technique:
        ...
