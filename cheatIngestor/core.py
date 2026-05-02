from cheatIngestor.ports.drivers.forDocumentIngestion import ForDocumentIngestion
from cheatIngestor.ports.drivers.forAutoCompletation import ForAutoComplete
from cheatIngestor.ports.drivens.forRepository import ForRepository
from cheatIngestor.models.template import Technique

# Caso de uso puro (hexágono interno), no implementa interfaces de drivers
class IngestorUseCase:
    def __init__(self, documents:ForDocumentIngestion,auto:ForAutoComplete):
        self.documents = documents
        self.auto = auto#repository: ForRepository):

    def ingest_document(self, document: str):
        # Lógica de negocio para ingestión
        self.documents.save_document(document)

    def search_techniques(self, keyword: str) -> Technique:
        return self.auto.searchCoincidence(keyword)
        # return technique
        