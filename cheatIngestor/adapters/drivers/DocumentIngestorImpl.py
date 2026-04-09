from cheatIngestor.ports.drivers.forDocumentIngestion import ForDocumentIngestion
from cheatIngestor.models.template import Technique
from cheatIngestor.ports.drivens.forRepository import ForRepository
import json
import io
class DocumentIngestorImp(ForDocumentIngestion):
    def __init__(self, repository: ForRepository):
        self.repository = repository

    def ingestJsonDocument(self,document:str) -> Technique:
        # document at this point should be a path 
        try:
            with open(document,'r') as rds:
                document = rds.read()
        except json.JSONDecodeError:
            raise ValueError('File Error JSON cant parse the data!')
        except Exception as e :
            raise ValueError(f'The file cant be loaded! {document} {e}')
        return self.repository.save_document(document)