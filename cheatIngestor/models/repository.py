from cheatIngestor.models.template import Template,Technique
class Configurator:
    
    def __init__(self,enabelSemanticSearch:bool,repository,dao):
        self.enabelSemanticSearch = enabelSemanticSearch
        self.repository = repository
        self.dao = dao