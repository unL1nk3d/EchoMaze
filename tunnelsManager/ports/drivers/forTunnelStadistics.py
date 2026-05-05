from abc import ABC, abstractmethod
from typing import Dict

class ForTunnelStadistics(ABC):
    @abstractmethod
    def get_tunnel_stats(self) -> Dict[str, int]:
        """Devuelve un resumen de estadísticas de los túneles (totales, colgantes, activos, etc.)"""
        pass
