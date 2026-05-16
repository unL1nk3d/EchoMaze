from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider
import os
import json

from agenticLLM.adapters.drivens.BaseLLMAdapter import BaseLLMAdapter

class LlamaCppAdapter(BaseLLMAdapter):
    """
    Adapter for llama-cpp-python to run models like DeepSeek locally.
    """
    def __init__(self, model_path: str, n_ctx: int = 4096, use_react: bool = False):
        super().__init__(use_react=use_react)
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("llama-cpp-python is not installed. Please install it with 'pip install llama-cpp-python'")
            
        if not os.path.exists(model_path):
            # Fallback to an environment variable or a default path for development
            model_path = os.getenv("LLAMA_MODEL_PATH", "models/deepseek-coder-6.7b-instruct.Q4_K_M.gguf")
            if not os.path.exists(model_path):
                print(f"Warning: Model path {model_path} not found. Agent will fail if called.")

        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=-1 # Use GPU if available
        )

    def _get_internal_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        # Convert domain messages to llama-cpp format (ChatML or similar)
        # DeepSeek Instruct usually likes:
        # User: {prompt}\n\nAssistant:
        
        prompt = ""
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            if msg.role == "system":
                prompt += f"System: {msg.content}\n\n"
            else:
                prompt += f"{role}: {msg.content}\n\n"
        
        prompt += "Assistant: "

        # Generate
        output = self.llm(
            prompt,
            max_tokens=1024,
            stop=["User:", "System:"],
            echo=False
        )

        content = output['choices'][0]['text'].strip()
        
        # Simple tool call detection (simulated for local GGUF)
        # In a real agentic setup with LlamaCpp, we might use grammars or regex
        tool_call_id = None
        if "ACTION:" in content:
            # Logic to extract tool_call_id and parameters would go here
            pass

        return Message(role="assistant", content=content, tool_call_id=tool_call_id)
