from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class AgentStep:
    agent_name: str
    stage: str # 'REASONING', 'TOOL_CALL', 'DELEGATION', 'OBSERVATION', 'COMPLETE'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentTrace:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.steps: List[AgentStep] = []
        self._start_time = datetime.now()

    def add_step(self, stage: str, content: str, **kwargs):
        step = AgentStep(
            agent_name=self.agent_name,
            stage=stage,
            content=content,
            metadata=kwargs
        )
        self.steps.append(step)
        return step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "start_time": self._start_time.isoformat(),
            "steps": [vars(s) for s in self.steps]
        }

class TraceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TraceManager, cls).__new__(cls)
            cls._instance._traces: Dict[str, AgentTrace] = {}
            cls._instance._subscribers = []
            cls._instance._active_parent: Optional[str] = None
        return cls._instance

    def set_active_parent(self, name: Optional[str]):
        """Sets the current primary agent being tracked (usually for UI)."""
        self._active_parent = name

    def get_trace(self, agent_name: str) -> AgentTrace:
        if agent_name not in self._traces:
            self._traces[agent_name] = AgentTrace(agent_name)
        return self._traces[agent_name]

    def add_step(self, agent_name: str, stage: str, content: str, **kwargs):
        trace = self.get_trace(agent_name)
        step = trace.add_step(stage, content, **kwargs)
        
        # If this is a delegated agent, also notify parent subscribers
        self._notify_subscribers(step)
        return step

    def subscribe(self, callback):
        """Subscribe to real-time trace updates."""
        self._subscribers.append(callback)

    def _notify_subscribers(self, step: AgentStep):
        for sub in self._subscribers:
            try:
                sub(step)
            except:
                pass
    
    def get_all_steps_since(self, agent_name: str, start_time: datetime) -> List[AgentStep]:
        """Returns all steps for this agent and its orchestrated sub-agents."""
        all_relevant_steps = []
        for name, trace in self._traces.items():
            if name == agent_name or name.startswith(f"orchestrated_"):
                all_relevant_steps.extend([s for s in trace.steps if s.timestamp >= start_time.isoformat()])
        
        return sorted(all_relevant_steps, key=lambda x: x.timestamp)

    def clear_traces(self):
        self._traces = {}
