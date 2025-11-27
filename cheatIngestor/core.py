from cheatIngestor.ports.drivers.forDocumentIngestion import ForDocumentIngestion
from cheatIngestor.ports.drivers.forAutoCompletation import ForAutoComplete
from cheatIngestor.ports.drivens.forRepository import ForRepository
from cheatIngestor.models.template import Technique
class Ingestor(ForDocumentIngestion,ForAutoComplete):
    def __init__(self,repository:ForRepository):
        super().__init__()
        self.repository = repository
    def ingestJsonDocument(self, document:str):
        self.repository.initialize_repository()
        self.repository.save_document(
            document
        )
    def searchCoincidence(self, keyword:str):
        technique:Technique =self.repository.search_coincidence(
            keyword
        )
        return technique.serialize()
        