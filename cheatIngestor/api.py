from cheatIngestor.core import IngestorUseCase
from cheatIngestor.adapters.drivers.DocumentIngestorImpl import DocumentIngestorImp
from cheatIngestor.adapters.drivers.Autocomplete import AutoCompleter
from cheatIngestor.adapters.drivens.RepositoryImpl import Repository
from cheatIngestor.models.repository import Configurator

def get_ingestor(dao=None):
    if dao is None:
        from GATHERINGDB.main import GenericDAO
        dao = GenericDAO()
    repo = Repository()
    config = Configurator(enabelSemanticSearch=False, repository=repo, dao=dao)
    repo.initialize_repository(config)
    doc_ingestor = DocumentIngestorImp(repository=repo)
    auto_completer = AutoCompleter(repository=repo)
    return IngestorUseCase(documents=doc_ingestor, auto=auto_completer)

def get_noise_estimate_for_command(command: str, dao=None) -> float:
    ingestor = get_ingestor(dao)
    technique = ingestor.search_techniques(command)
    if technique and hasattr(technique, 'templates') and technique.templates:
        for t in technique.templates:
            if hasattr(t, 'noise_estimate') and t.noise_estimate is not None:
                try:
                    return float(t.noise_estimate)
                except ValueError:
                    pass
    return None
