from abc import ABC, abstractmethod

class ForConnectionTest(ABC):
    @abstractmethod
    def test_local_port_open(self, port: int) -> bool:
        """Comprueba si un puerto local está efectivamente abierto."""
        pass
