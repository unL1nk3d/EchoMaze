from abc import ABC, abstractmethod
from typing import Dict

class ForTunnelStadistics(ABC):
    @abstractmethod
    def get_tunnel_stats(self) -> Dict[str, int]:
        """Devuelve un resumen de estadísticas de los túneles (totales, colgantes, activos, etc.)"""
        pass

    @abstractmethod
    def register_data_transfer(self, tunnel_id: int, sent_bytes: int, received_bytes: int) -> bool:
        """Registra la transferencia de datos para un túnel específico."""
        pass

    @abstractmethod
    def get_tunnel_metrics(self, tunnel_id: int) -> Dict[str, any]:
        """Obtiene métricas detalladas de transferencia para un túnel."""
        pass

    @abstractmethod
    def evaluate_tunnel_entropy(self, tunnel_id: int) -> bool:
        """Evalúa el túnel usando algoritmos de entropía y actualiza su score/warning."""
        pass
