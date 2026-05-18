import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider

class BaseLLMAdapter(ForLLMProvider, ABC):
    """
    Base class for all LLM adapters in EchoMaze.
    Provides shared logic for ReAct (manual tool parsing) and native tool handling.
    """
    def __init__(self, use_react: bool = False):
        self.use_react = use_react

    def generate_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        if self.use_react and tools:
            # 1. Prepare the ReAct system prompt
            react_instructions = self._get_react_instructions(tools)
            
            # 2. Inject instructions into the first system message or add a new one
            modified_messages = self._inject_instructions(messages, react_instructions)
            
            # 3. Get raw text response from the subclass (calling it without tools)
            response = self._get_internal_response(modified_messages, [])
            
            # 4. Parse for tool calls in the content
            tool_call = self._parse_tool_call(response.content)
            
            if tool_call:
                response.tool_call_id = f"react_{tool_call['name']}"
                response.name = tool_call['name']
                response.tool_arguments = tool_call['arguments']
                # We keep the original response.content as it is (likely containing the thought + JSON)
            
            return response
        else:
            # Normal native tool handling
            return self._get_internal_response(messages, tools)

    @abstractmethod
    def _get_internal_response(self, messages: List[Message], tools: List[Tool]) -> Message:
        """Subclasses implement the actual API call (Ollama, llama-cpp, etc.)"""
        pass

    def _get_react_instructions(self, tools: List[Tool]) -> str:
        tools_desc = "\n".join([f"- {t.name}: {t.description}. Parameters: {json.dumps(t.parameters)}" for t in tools])
        
        return f"""
# TOOL USE INSTRUCTIONS
You have access to the following tools:
{tools_desc}

To use a tool, you MUST respond with a JSON block in the following format:
```json
{{
  "action": "tool_name",
  "action_input": {{ "arg1": "value1", ... }}
}}
```

Wait for the tool output before continuing. If you have the final answer, just respond normally.
"""

    def _inject_instructions(self, messages: List[Message], instructions: str) -> List[Message]:
        new_messages = [msg for msg in messages]
        
        # Find system message or add it
        system_msg = next((m for m in new_messages if m.role == "system"), None)
        if system_msg:
            # Create a new message to avoid mutating the original history objects if shared
            system_msg = Message(role="system", content=system_msg.content + f"\n\n{instructions}")
            # Replace in our local copy
            for i, m in enumerate(new_messages):
                if m.role == "system":
                    new_messages[i] = system_msg
                    break
        else:
            new_messages.insert(0, Message(role="system", content=instructions))
            
        return new_messages

    def _parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
            
        # Look for JSON blocks
        pattern = r"```json\s*(.*?)\s*```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if "action" in data and "action_input" in data:
                    return {
                        "name": data["action"],
                        "arguments": data["action_input"]
                    }
            except json.JSONDecodeError:
                continue
        
        # Fallback: try to find any JSON-like structure if no code blocks
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                data = json.loads(content[start:end])
                if "action" in data and "action_input" in data:
                    return {
                        "name": data["action"],
                        "arguments": data["action_input"]
                    }
        except:
            pass
            
        return None
