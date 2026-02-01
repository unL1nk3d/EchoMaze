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
            with open(self.document,'r') as rds:
                result = json.loads(rds.read())
        except json.JSONDecodeError:
            raise ValueError('File Error JSON cant parse the data!')
        except:
            raise ValueError('The file cant be loaded!')
        return self.repository.save_document(document)