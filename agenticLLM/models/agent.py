from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Message:
    role: str # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any] # JSON Schema
    requires_approval: bool = False

@dataclass
class PendingAction:
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]

@dataclass
class AgentConfig:
    model_name: str = "gpt-4o"
    temperature: float = 0.0
    system_prompt: str = (
        "You are EchoMaze AI, an expert penetration testing assistant. "
        "You MUST follow the Lockheed Martin Cyber Kill Chain methodology for all operations. "
        "The phases are: Reconnaissance, Weaponization, Delivery, Exploitation, Installation, Command and Control, and Actions on Objectives. "
        "Always track the current phase of each target IP using the 'set_cyber_kill_chain_phase' tool. "
        "Before suggesting actions, check the current phase using 'get_cyber_kill_chain_status'. "
        "Maintain a structured approach and document your findings in the operational memory."
    )

class AgentState:
    def __init__(self):
        self.history: List[Message] = []
        self.available_tools: List[Tool] = []
        self.pending_action: Optional[PendingAction] = None

@dataclass
class OperationalMemory:
    id: Optional[int] = None
    content: str = ""
    source: str = "" # e.g., 'user_note', 'tool_output', 'agent_finding'
    timestamp: str = ""
    phase: str = "Reconnaissance" # Lockheed Martin Cyber Kill Chain phase
    metadata: Dict[str, Any] = field(default_factory=dict)

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
