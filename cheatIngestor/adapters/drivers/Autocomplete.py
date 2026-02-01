from cheatIngestor.ports.drivers.forAutoCompletation import ForAutoComplete
from cheatIngestor.models.template import Technique
from cheatIngestor.ports.drivens.forRepository import ForRepository
class AutoCompleter(ForAutoComplete):
    def __init__(self, repository: ForRepository):
        self.repository = repository

    def searchCoincidence(self, keyword: str) -> Technique:
        return self.repository.search_coincidence(keyword)