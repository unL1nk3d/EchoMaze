from cheatIngestor.ports.drivens.forRepository import ForRepository
from cheatIngestor.models.repository import Configurator
from cheatIngestor.models.template import Technique,Template
from json import loads
class Repository(ForRepository):
    _configurator:Configurator = None
    def __init__(self):
        self.configurator:Configurator = None
        super().__init__()
    def initialize_repository(self, configuration:Configurator):
        if Repository._configurator == None:
            Repository._configurator = configuration
            self.configurator:Configurator = Repository._configurator
        
        
    def save_document(self, document:str):
        
        tmp = loads(document)
        
        for technique in tmp['techniques']:
            templates = []
            Technique(
                technique['technique'],
                technique["name"],
                templates
            )
            for temp in tmp['templates']:
                
                templates.append(Template(
                    tmp["desc"],
                    tmp["windows"],
                    tmp["linux"],
                    tmp["noise_estimate"],
                ))
                
        self.configurator.repository.insert_template(
                ...
        )
        self.insert_template(self.document)

    def search_coincidence(self, text):
        raise NotImplementedError

    def insert_template(self, technique, name, desc, linux, windows, noise_estimate = 0):
        ...

    def select_all_templates(self):
        raise NotImplementedError

    def select_template_by_technique(self, technique):
        raise NotImplementedError

    def update_template(self, technique, name = None, desc = None, linux = None, windows = None, noise_estimate = None):
        raise NotImplementedError

    def delete_template(self, technique):
        raise NotImplementedError

    