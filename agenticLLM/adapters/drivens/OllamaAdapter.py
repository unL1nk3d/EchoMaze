from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider
import json
import urllib.request
import urllib.error

from agenticLLM.adapters.drivens.BaseLLMAdapter import BaseLLMAdapter

class OllamaAdapter(BaseLLMAdapter):
    """
    Adapter for Ollama API, allowing EchoMaze to use local models via Ollama.
    """
    def __init__(self, model_name: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434", use_react: bool = False):
        super().__init__(use_react=use_react)
        self.model_name = model_name
        self.base_url = base_url

    def _get_internal_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        # Ensure no trailing slash in base_url
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/api/chat"
        
        # Convert domain messages to Ollama format
        ollama_messages = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content or ""}
            
            # If it was an assistant message with a tool call, we MUST format it with tool_calls for Ollama
            if msg.role == "assistant" and msg.tool_call_id:
                try:
                    # In EchoMaze, assistant messages with tool_calls store arguments in content
                    args = json.loads(msg.content) if msg.content else {}
                    m["tool_calls"] = [{
                        "type": "function",
                        "function": {
                            "name": msg.name,
                            "arguments": args
                        }
                    }]
                    # Content usually empty when tool_calls is present
                    m["content"] = ""
                except Exception:
                    pass
            
            # If it's a tool result, provide the tool_call_id for context
            if msg.role == "tool" and msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
                
            ollama_messages.append(m)
            
        # Ollama supports tools in the chat API (for compatible models like llama3.1, mistral, etc.)
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        
        data = {
            "model": self.model_name,
            "messages": ollama_messages,
            "stream": False
        }
        
        if ollama_tools:
            data["tools"] = ollama_tools
        
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                message_data = res_data.get('message', {})
                content = message_data.get('content') or "" # Ensure it's a string, never None
                tool_calls = message_data.get('tool_calls', [])
                
                if tool_calls:
                    # EchoMaze AgentUseCase currently expects one tool call at a time via tool_call_id
                    # We'll take the first one and map it accordingly.
                    first_tool = tool_calls[0]
                    tool_name = first_tool.get('function', {}).get('name')
                    tool_args = first_tool.get('function', {}).get('arguments', {})
                    
                    return Message(
                        role="assistant",
                        content=json.dumps(tool_args),
                        tool_call_id=f"ollama_{tool_name}",
                        name=tool_name
                    )

                return Message(role="assistant", content=content)
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                pass
            return Message(role="assistant", content=f"Error connecting to Ollama at {self.base_url}: {e}\nResponse: {error_body}")
        except urllib.error.URLError as e:
            return Message(role="assistant", content=f"Error connecting to Ollama at {self.base_url}: {e}")
        except Exception as e:
            return Message(role="assistant", content=f"Unexpected error calling Ollama: {e}")

    def list_available_models(self) -> List[str]:
        """Queries the Ollama API for a list of locally installed models."""
        base_url = self.base_url.rstrip('/')
        url = f"{base_url}/api/tags"
        try:
            with urllib.request.urlopen(url) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                models = res_data.get('models', [])
                return [m['name'] for m in models]
        except Exception as e:
            # We don't want to crash the UI if Ollama is down here
            return []
