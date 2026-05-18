from agenticLLM.core.agent_use_case import AgentUseCase
from agenticLLM.adapters.drivens.MockLLMAdapter import MockLLMAdapter
from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter
from agenticLLM.adapters.drivens.OperationalMemoryAdapter import InMemoryOperationalMemoryAdapter
from agenticLLM.adapters.drivens.SkillExecutorAdapter import CLISkillExecutorAdapter
from tunnelsManager import get_tunnels_api
import os

def get_agent_api(tunnels_api=None, llm_provider=None, generic_model=None, provider_type=None, memory_type='in_memory', use_react=None):
    """
    Factory to get the Agent API.
    
    provider_type: 'mock' (default), 'llamacpp', or 'ollama'
    memory_type: 'in_memory' (default) or 'hyperdb'
    use_react: boolean, if True forces ReAct (manual tool parsing). 
               Defaults to False for Ollama, True for LlamaCpp/Mock.
    """
    if not tunnels_api:
        tunnels_api = get_tunnels_api()
    
    if use_react is None:
        use_react = os.getenv("AGENT_USE_REACT", "false").lower() == "true"
        # Auto-enable ReAct for providers that usually don't support tools natively
        if provider_type in ['llamacpp', 'mock'] and os.getenv("AGENT_USE_REACT") is None:
            use_react = True

    if not llm_provider:
        if provider_type == 'llamacpp':
            from agenticLLM.adapters.drivens.LlamaCppAdapter import LlamaCppAdapter
            model_path = os.getenv("LLAMA_MODEL_PATH", "models/deepseek-coder.gguf")
            llm_provider = LlamaCppAdapter(model_path=model_path, use_react=use_react)
        elif provider_type == 'ollama':
            from agenticLLM.adapters.drivens.OllamaAdapter import OllamaAdapter
            model_name = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            llm_provider = OllamaAdapter(model_name=model_name, base_url=base_url, use_react=use_react)
        else:
            llm_provider = MockLLMAdapter(use_react=use_react)
        
    if memory_type == 'hyperdb':
        from agenticLLM.adapters.drivens.HyperDBAdapter import HyperDBOperationalMemoryAdapter
        memory_repo = HyperDBOperationalMemoryAdapter(db_path="operation_context.pickle.gz")
    else:
        memory_repo = InMemoryOperationalMemoryAdapter()
        
    skills_registry = CLISkillExecutorAdapter()
    tool_executor = SystemToolExecutorAdapter(tunnels_api, generic_model, skills_registry)
    agent = AgentUseCase(llm_provider, tool_executor, memory_repo, skills_registry)
    
    return agent

def get_agent_manager(tunnels_api=None, generic_model=None):
    """Factory to get the Agent Manager."""
    from agenticLLM.core.agent_manager_use_case import AgentManagerUseCase
    return AgentManagerUseCase(tunnels_api, generic_model)
