from abc import ABC, abstractmethod
from typing import List
from tunnelsManager.models.implant import Implant

class ForImplantRepository(ABC):
    @abstractmethod
    def save_implant(self, implant: Implant) -> Implant:
        pass

    @abstractmethod
    def list_implants(self) -> List[Implant]:
        pass

    @abstractmethod
    def get_implant(self, implant_id: int) -> Implant:
        pass

    @abstractmethod
    def delete_implant(self, implant_id: int) -> bool:
        pass
