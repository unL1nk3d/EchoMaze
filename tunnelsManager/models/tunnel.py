from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Tunnel:
    # Allowed statuses
    STATUS_ACTIVE = "active"
    STATUS_DISCONNECTED = "disconnected"
    STATUS_DEACTIVATED = "deactivated"
    STATUS_ACTIVATING = "activating"
    STATUS_FILTERED = "filtered connection"
    
    ALLOWED_STATUSES = [
        STATUS_ACTIVE, 
        STATUS_DISCONNECTED, 
        STATUS_DEACTIVATED, 
        STATUS_ACTIVATING, 
        STATUS_FILTERED
    ]

    # Allowed techniques
    TECHNIQUE_NONE = "none"
    TECHNIQUE_BEACONING = "beaconing"
    
    ALLOWED_TECHNIQUES = [TECHNIQUE_NONE, TECHNIQUE_BEACONING]

    id: Optional[int]
    source_ip: str
    dest_ip: Optional[str]
    local_port: int
    remote_port: Optional[int]
    status: str = STATUS_ACTIVE 
    technique: str = TECHNIQUE_NONE

    @property
    def is_hanging(self) -> bool:
        """Un túnel colgante es aquel que no está relacionado a ninguna dirección IP destino."""
        return not self.dest_ip or self.dest_ip.strip() == ""
