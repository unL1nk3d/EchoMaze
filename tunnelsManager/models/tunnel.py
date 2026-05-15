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

    # Phases for tunnel creation
    PHASE_CREATION = "tunnel creation"
    PHASE_SETTING_UP = "tunnel setting up"
    PHASE_INTERFACE_REGISTRATION = "interface registration"
    PHASE_READY_TO_SEND = "ready to send"

    ALLOWED_PHASES = [
        PHASE_CREATION,
        PHASE_SETTING_UP,
        PHASE_INTERFACE_REGISTRATION,
        PHASE_READY_TO_SEND
    ]

    # Allowed techniques
    TECHNIQUE_NONE = "none"
    TECHNIQUE_BEACONING = "beaconing"
    
    ALLOWED_TECHNIQUES = [TECHNIQUE_NONE, TECHNIQUE_BEACONING]

    # Tunnel Types
    TYPE_HTTP = "HTTP"
    TYPE_SOCKS4 = "SOCKS4"
    TYPE_SOCKS5 = "SOCKS5"
    TYPE_SHADOWSOCKS = "Shadowsocks"
    TYPE_STEGANOGRAPHY = "Steganography"
    TYPE_IMAGE_TUNNEL = "Image Tunnel"
    TYPE_DNS = "DNS"
    TYPE_ICMP = "ICMP"

    ALLOWED_TYPES = [
        TYPE_HTTP,
        TYPE_SOCKS4,
        TYPE_SOCKS5,
        TYPE_SHADOWSOCKS,
        TYPE_STEGANOGRAPHY,
        TYPE_IMAGE_TUNNEL,
        TYPE_DNS,
        TYPE_ICMP
    ]

    id: Optional[int] = None
    source_ip: str = ""
    dest_ip: Optional[str] = None
    local_port: int = 0
    remote_port: Optional[int] = None
    status: str = STATUS_ACTIVE 
    technique: str = TECHNIQUE_NONE
    phase: str = PHASE_CREATION
    tunnel_type: str = TYPE_HTTP
    data_sent_bytes: int = 0
    data_received_bytes: int = 0
    last_activity: Optional[str] = None
    entropy_score: float = 0.0
    entropy_warning: str = "No evaluation yet"
    data_type: str = "texto plano"
    implant_id: Optional[int] = None

    @property
    def is_hanging(self) -> bool:
        """Un túnel colgante es aquel que no está relacionado a ninguna dirección IP destino."""
        return not self.dest_ip or self.dest_ip.strip() == ""
