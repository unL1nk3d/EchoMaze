from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Message:
    role: str # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(**data)

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any] # JSON Schema
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tool':
        return cls(**data)

@dataclass
class PendingAction:
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PendingAction':
        return cls(**data)

@dataclass
class AgentConfig:
    model_name: str = "gpt-4o"
    temperature: float = 0.0
    system_prompt: str = ""

    def __post_init__(self):
        if not self.system_prompt:
            from agenticLLM.core.prompt_manager import PromptManager
            self.system_prompt = PromptManager().get_prompt("default")

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        return cls(**data)

class AgentState:
    def __init__(self):
        self.history: List[Message] = []
        self.available_tools: List[Tool] = []
        self.pending_action: Optional[PendingAction] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": [m.to_dict() for m in self.history],
            "available_tools": [t.to_dict() for t in self.available_tools],
            "pending_action": self.pending_action.to_dict() if self.pending_action else None
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

@dataclass
class OperationalMemory:
    id: Optional[int] = None
    content: str = ""
    source: str = "" # e.g., 'user_note', 'tool_output', 'agent_finding'
    timestamp: str = ""
    phase: str = "Reconnaissance" # Lockheed Martin Cyber Kill Chain phase
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationalMemory':
        return cls(**data)

class CyberKillChain:
    RECONNAISSANCE = "Reconnaissance"
    WEAPONIZATION = "Weaponization"
    DELIVERY = "Delivery"
    EXPLOITATION = "Exploitation"
    INSTALLATION = "Installation"
    COMMAND_AND_CONTROL = "Command and Control"
    ACTIONS_ON_OBJECTIVES = "Actions on Objectives"
    
    PHASES = [
        RECONNAISSANCE, WEAPONIZATION, DELIVERY, EXPLOITATION, 
        INSTALLATION, COMMAND_AND_CONTROL, ACTIONS_ON_OBJECTIVES
    ]

@dataclass
class Skill:
    name: str
    description: str
    usage_example: str
    category: str = "general" # e.g., 'discovery', 'exploitation', 'utility'
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        return cls(**data)
