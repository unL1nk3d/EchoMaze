from cheatIngestor.ports.drivens.forRepository import ForRepository
from cheatIngestor.models.repository import Configurator
from cheatIngestor.models.template import Technique,Template
from json import loads
from GATHERINGDB.model import Templates
import sqlite3
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
        # Asumir formato: {"technique": "T1021", "name": "Pivoting", "templates": [{"desc": "...", "linux": "...", "windows": "...", "noise_estimate": 5}]}
        technique = tmp['technique']
        name = tmp['name']
        for temp in tmp['templates']:
            self.insert_template(technique, name, temp["desc"], temp["linux"], temp["windows"], temp["noise_estimate"])
        
            
            

    def search_coincidence(self, text) -> Technique:
        # Usar FTS para búsqueda
        try:
            results = self.configurator.dao.seleccionarCoincidenciaFTS(Templates, text)
        except sqlite3.OperationalError:
            results = []
            
        templates = []
        for row in results:
            templates.append(Template(row[2], row[3], row[4], row[5]))  # desc, linux, windows, noise_estimate
        return Technique("", "", templates) # Simplificado

    def insert_template(self, technique, name, desc, linux, windows, noise_estimate = 0):
        template = Templates(technique, name, desc, linux, windows, noise_estimate)
        self.configurator.dao.insertar(template)


    def select_all_templates(self):
        return self.configurator.dao.seleccionar(Templates)
    def select_template_by_technique(self, technique):
        return self.configurator.dao.seleccionarCoincidencia(Templates, 'technique', technique)

    def update_template(self, technique, name = None, desc = None, linux = None, windows = None, noise_estimate = None):
        # Implementar update
        pass

    def delete_template(self, technique):
        # Implementar delete
        pass
    