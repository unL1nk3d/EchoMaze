from typing import List, Dict, Any, Optional
from agenticLLM.ports.drivers.forAgentManagement import ForAgentManagement
from agenticLLM.ports.drivers.forAgentInteraction import ForAgentInteraction
from agenticLLM.api import get_agent_api
from agenticLLM.models.agent import AgentConfig
from agenticLLM.core.prompt_manager import PromptManager

class AgentManagerUseCase(ForAgentManagement):
    def __init__(self, tunnels_api=None, generic_model=None, default_provider: str = "mock"):
        self._agents: Dict[str, ForAgentInteraction] = {}
        self.tunnels_api = tunnels_api
        self.generic_model = generic_model
        self.default_provider = default_provider
        self.prompt_manager = PromptManager()
        self._personas: Dict[str, AgentConfig] = self._load_personas_from_manager()

    def _load_personas_from_manager(self) -> Dict[str, AgentConfig]:
        personas = {}
        for key in self.prompt_manager.list_keys():
            personas[key] = AgentConfig(persona_name=key, system_prompt=self.prompt_manager.get_prompt(key))
        return personas

    def create_agent(self, name: str, persona: str = "general", provider: Optional[str] = None, tools_file: Optional[str] = None) -> ForAgentInteraction:
        if name in self._agents:
            return self._agents[name]
        
        # Use provided provider, or fallback to the manager's default provider
        active_provider = provider or self.default_provider
        
        # Refresh personas in case PromptManager was updated
        self._personas = self._load_personas_from_manager()
        config = self._personas.get(persona, AgentConfig(persona_name=persona))
        
        # Use the existing factory to get an agent instance
        agent = get_agent_api(
            tunnels_api=self.tunnels_api,
            llm_provider=None, 
            generic_model=self.generic_model,
            provider_type=active_provider,
            name=name
        )
        
        # Override the agent's config with the persona's config
        agent.config = config
        # Reset history to apply the new system prompt
        agent.reset()
        
        # Load extra tools if provided
        if tools_file and hasattr(agent.tools_executor, 'load_tools_from_file'):
            agent.tools_executor.load_tools_from_file(tools_file)
            # Update available tools list in agent state
            agent.state.available_tools = agent.tools_executor.list_tools()

        self._agents[name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[ForAgentInteraction]:
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    def delete_agent(self, name: str):
        if name in self._agents:
            del self._agents[name]

    def add_persona(self, persona_name: str, config: AgentConfig):
        self._personas[persona_name] = config
