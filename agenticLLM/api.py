from agenticLLM.core.agent_use_case import AgentUseCase
from agenticLLM.adapters.drivens.MockLLMAdapter import MockLLMAdapter
from agenticLLM.adapters.drivens.ToolExecutorAdapter import SystemToolExecutorAdapter
from agenticLLM.adapters.drivens.OperationalMemoryAdapter import InMemoryOperationalMemoryAdapter
from agenticLLM.adapters.drivens.SkillExecutorAdapter import CLISkillExecutorAdapter
from tunnelsManager import get_tunnels_api
import os

def get_agent_api(tunnels_api=None, llm_provider=None, generic_model=None, provider_type=None, memory_type='in_memory'):
    """
    Factory to get the Agent API.
    
    provider_type: 'mock' (default) or 'llamacpp'
    memory_type: 'in_memory' (default) or 'hyperdb'
    """
    if not tunnels_api:
        tunnels_api = get_tunnels_api()
    
    if not llm_provider:
        if provider_type == 'llamacpp':
            from agenticLLM.adapters.drivens.LlamaCppAdapter import LlamaCppAdapter
            model_path = os.getenv("LLAMA_MODEL_PATH", "models/deepseek-coder.gguf")
            llm_provider = LlamaCppAdapter(model_path=model_path)
        else:
            llm_provider = MockLLMAdapter()
        
    if memory_type == 'hyperdb':
        from agenticLLM.adapters.drivens.HyperDBAdapter import HyperDBOperationalMemoryAdapter
        memory_repo = HyperDBOperationalMemoryAdapter(db_path="operation_context.pickle.gz")
    else:
        memory_repo = InMemoryOperationalMemoryAdapter()
        
    skills_registry = CLISkillExecutorAdapter()
    tool_executor = SystemToolExecutorAdapter(tunnels_api, generic_model, skills_registry)
    agent = AgentUseCase(llm_provider, tool_executor, memory_repo, skills_registry)
    
    return agent
