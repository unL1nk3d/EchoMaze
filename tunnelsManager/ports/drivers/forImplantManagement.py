from abc import ABC, abstractmethod
from typing import List
from tunnelsManager.models.implant import Implant

class ForImplantManagement(ABC):
    @abstractmethod
    def create_implant(self, name: str, implant_type: str, payload: str, description: str = "", supported_tunnel_type: str = None) -> Implant:
        """Crea y registra un nuevo implante en el sistema."""
        pass

    @abstractmethod
    def list_implants(self) -> List[Implant]:
        """Obtiene la lista de todos los implantes disponibles."""
        pass

    @abstractmethod
    def get_implant(self, implant_id: int) -> Implant:
        """Obtiene un implante específico por su ID."""
        pass

    @abstractmethod
    def delete_implant(self, implant_id: int) -> bool:
        """Elimina un implante del sistema."""
        pass

    @abstractmethod
    def generate_payload(self, implant_type: str, listener_ip: str, listener_port: int) -> str:
        """Genera un payload base según el tipo y parámetros."""
        pass
