import json
from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool, AgentState, AgentConfig, PendingAction
from agenticLLM.ports.drivers.forAgentInteraction import ForAgentInteraction
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider, ForToolExecution
from agenticLLM.ports.drivens.forOperationalMemory import ForOperationalMemoryRepository
from agenticLLM.ports.drivens.forSkills import ForSkillRegistry

class AgentUseCase(ForAgentInteraction):
    def __init__(self, llm: ForLLMProvider, tools: ForToolExecution, memory_repo: ForOperationalMemoryRepository, skills: ForSkillRegistry, config: AgentConfig = None):
        self.llm = llm
        self.tools_executor = tools
        self.memory_repo = memory_repo
        self.skills_registry = skills
        self.config = config or AgentConfig()
        self.state = AgentState()
        
        # Link skills to tool executor if not already linked
        if hasattr(self.tools_executor, 'skills_registry'):
            self.tools_executor.skills_registry = self.skills_registry
            
        self.state.available_tools = self.tools_executor.list_tools()
        
        # Initialize history with system prompt
        self.state.history.append(Message(role="system", content=self.config.system_prompt))

    def ask(self, user_input: str) -> str:
        # Clear any old pending action
        self.state.pending_action = None
        
        # 1. RAG Step: Retrieve relevant memories
        relevant_memories = self.memory_repo.search_memories(user_input)
        if relevant_memories:
            context_str = "\n".join([f"- {m.content}" for m in relevant_memories])
            rag_message = f"Relevant operational context found:\n{context_str}\n\nUse this information to answer the user query: {user_input}"
            self.state.history.append(Message(role="user", content=rag_message))
        else:
            self.state.history.append(Message(role="user", content=user_input))
        
        return self._run_loop()

    def _run_loop(self) -> str:
        max_iterations = 5
        for _ in range(max_iterations):
            # 1. Get response from LLM
            assistant_msg = self.llm.generate_response(self.state.history, self.state.available_tools)
            self.state.history.append(assistant_msg)
            
            # 2. Check if it's a tool call
            if not assistant_msg.tool_call_id:
                return assistant_msg.content
            
            # 3. Find the tool to see if it requires approval
            tool_name = assistant_msg.name or ""
            target_tool = next((t for t in self.state.available_tools if t.name == tool_name), None)
            
            # Get arguments from new field or fallback to content
            arguments = assistant_msg.tool_arguments or {}
            if not arguments and assistant_msg.content:
                try:
                    arguments = json.loads(assistant_msg.content)
                except:
                    pass

            # Check for duplicate identical tool calls in the last few messages to avoid infinite loops
            # If the model repeats the exact same call with the exact same args immediately, it's stuck.
            if len(self.state.history) > 3:
                last_tool_msgs = [m for m in self.state.history[-4:-1] if m.role == "assistant" and m.tool_call_id]
                for prev in last_tool_msgs:
                    if prev.name == tool_name and prev.tool_arguments == arguments:
                         return f"Agent stuck in a loop calling {tool_name}. Stopping to avoid resource waste."

            if target_tool and target_tool.requires_approval:
                self.state.pending_action = PendingAction(
                    tool_call_id=assistant_msg.tool_call_id,
                    tool_name=tool_name,
                    arguments=arguments
                )
                return f"[WAITING_FOR_APPROVAL]: The agent wants to execute {tool_name}. Do you allow it?"

            # 4. Execute tool directly if no approval required
            result = self.tools_executor.execute_tool(tool_name, arguments)
            self.state.history.append(Message(role="tool", content=result, tool_call_id=assistant_msg.tool_call_id, name=tool_name))
            
        return "Max iterations reached without final response."

    def get_pending_action(self) -> Optional[Dict[str, Any]]:
        if not self.state.pending_action:
            return None
        return {
            "tool_name": self.state.pending_action.tool_name,
            "arguments": self.state.pending_action.arguments
        }

    def provide_approval(self, approved: bool) -> str:
        if not self.state.pending_action:
            return "No pending action to approve."
        
        action = self.state.pending_action
        self.state.pending_action = None
        
        if approved:
            result = self.tools_executor.execute_tool(action.tool_name, action.arguments)
            self.state.history.append(Message(role="tool", content=result, tool_call_id=action.tool_call_id, name=action.tool_name))
            return self._run_loop()
        else:
            self.state.history.append(Message(role="tool", content="Action rejected by operator.", tool_call_id=action.tool_call_id, name=action.tool_name))
            return self._run_loop()

    def get_history(self) -> List[Message]:
        return self.state.history

    def get_tools_json(self) -> str:
        import json
        return json.dumps([t.to_dict() for t in self.state.available_tools], indent=2)

    def compact_history(self) -> str:
        """
        Generates a summary of the current history, saves it to RAG,
        and resets the history to just the summary to save context space.
        """
        if len(self.state.history) <= 2: # System + 1 message isn't worth compacting
            return "History is too short to compact."

        # 1. Prepare summarization prompt
        history_str = ""
        for msg in self.state.history:
            if msg.role == "system": continue
            role = "User" if msg.role == "user" else "Assistant"
            if msg.role == "tool": role = "Tool Output"
            history_str += f"{role}: {msg.content}\n"

        summary_prompt = (
            "You are a summarization assistant. Provide a concise but comprehensive summary "
            "of the following penetration testing conversation. Focus on: \n"
            "1. Discovered assets and vulnerabilities.\n"
            "2. Actions performed and their results.\n"
            "3. Current progress in the Cyber Kill Chain.\n\n"
            f"CONVERSATION HISTORY:\n{history_str}\n\n"
            "SUMMARY:"
        )

        # 2. Get summary from LLM (using a clean history for the summarization call)
        temp_history = [Message(role="system", content=summary_prompt)]
        summary_msg = self.llm.generate_response(temp_history, [])
        summary_text = summary_msg.content

        # 3. Save to RAG
        from agenticLLM.models.agent import OperationalMemory
        memory = OperationalMemory(
            content=f"Conversation Summary: {summary_text}",
            source="history_compaction",
            metadata={"compacted_at": len(self.state.history)}
        )
        self.memory_repo.save_memory(memory)

        # 4. Reset history
        compacted_context = (
            "The following is a summary of the previous conversation context. "
            "Use this to continue the operation efficiently:\n\n"
            f"{summary_text}"
        )
        
        self.state.history = [
            Message(role="system", content=self.config.system_prompt),
            Message(role="system", content=compacted_context)
        ]

        return "History compacted and saved to operational memory."

    def reset(self):
        self.state.history = [Message(role="system", content=self.config.system_prompt)]
        self.state.pending_action = None
