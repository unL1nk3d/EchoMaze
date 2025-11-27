from abc import ABC,abstractmethod
from cheatIngestor.models.template import Technique,Template
class ForRepository(ABC):
    @abstractmethod
    def initialize_repository(self,configuration):
        ...
    @abstractmethod
    def save_document(self,document:str) -> Technique:
        # json document
        ...
    @abstractmethod
    def search_coincidence(self,text:str) ->Technique:
        ...
    @abstractmethod
    def insert_template(self, technique: str, name: str, desc: str,
                        linux: str, windows: str, noise_estimate: float = 0.0,) -> Template:
        """Insertar un template nuevo"""
        ...
    @abstractmethod
    def select_all_templates(self) -> Technique:
        """Devolver todos los templates"""
        ...
    @abstractmethod
    def select_template_by_technique(self, technique: str) -> Template:
        """Buscar template por su técnica (clave)"""
        ...
    @abstractmethod
    def update_template(self, technique: str, name: str = None, desc: str = None,
                        linux: str = None, windows: str = None, noise_estimate: float = None) -> Template:
        """Actualizar campos de un template existente"""
        ...
    @abstractmethod
    def delete_template(self, technique: str):
        """Eliminar un template por técnica"""
        ...