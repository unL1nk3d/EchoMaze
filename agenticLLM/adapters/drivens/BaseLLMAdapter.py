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
        # For ReAct, we also need to ensure all 'tool' messages are converted to 'user' messages
        # because the LLM won't understand the 'tool' role without native tool support.
        new_messages = []
        for msg in messages:
            if msg.role == "tool":
                # Convert tool output to a user message for the LLM
                new_messages.append(Message(role="user", content=f"[TOOL OUTPUT from {msg.name}]:\n{msg.content}"))
            else:
                new_messages.append(Message(role=msg.role, content=msg.content, tool_call_id=msg.tool_call_id, name=msg.name, tool_arguments=msg.tool_arguments))
        
        # Find system message or add it
        system_msg_idx = -1
        for i, m in enumerate(new_messages):
            if m.role == "system":
                system_msg_idx = i
                break
                
        if system_msg_idx != -1:
            orig = new_messages[system_msg_idx]
            new_messages[system_msg_idx] = Message(role="system", content=orig.content + f"\n\n{instructions}")
        else:
            new_messages.insert(0, Message(role="system", content=instructions))
            
        return new_messages

    def _parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
            
        # 1. Try to find JSON blocks first
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
        
        # 2. Fallback: Search for the first '{' and the last '}' that contains 'action' and 'action_input'
        try:
            # Clean think tags for more reliable fallback parsing
            clean_content = content
            if "<think>" in content and "</think>" in content:
                clean_content = content.split("</think>")[-1]

            # Look for the last JSON-like block (often tools are at the end)
            start_indices = [i for i, char in enumerate(clean_content) if char == '{']
            for start in reversed(start_indices):
                end = clean_content.find('}', start) + 1
                if end > 0:
                    try:
                        data = json.loads(clean_content[start:end])
                        if "action" in data and "action_input" in data:
                            return {
                                "name": data["action"],
                                "arguments": data["action_input"]
                            }
                    except:
                        continue
        except:
            pass
            
        return None
