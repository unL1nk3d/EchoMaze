from dataclasses import dataclass
from typing import Optional

@dataclass
class Implant:
    TYPE_PYTHON = "python"
    TYPE_POWERSHELL = "powershell"
    TYPE_BINARY_EXE = "binary_exe"
    TYPE_BINARY_ELF = "binary_elf"
    TYPE_STAGER = "stager"

    ALLOWED_TYPES = [TYPE_PYTHON, TYPE_POWERSHELL, TYPE_BINARY_EXE, TYPE_BINARY_ELF, TYPE_STAGER]

    id: Optional[int] = None
    name: str = ""
    implant_type: str = TYPE_PYTHON
    payload: str = ""
    description: str = ""
    created_at: Optional[str] = None
    supported_tunnel_type: Optional[str] = None
