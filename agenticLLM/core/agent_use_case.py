import json
from typing import List, Dict, Any, Optional
from agenticLLM.models.agent import Message, Tool, AgentState, AgentConfig, PendingAction
from agenticLLM.ports.drivers.forAgentInteraction import ForAgentInteraction
from agenticLLM.ports.drivens.forLLMAndTools import ForLLMProvider, ForToolExecution
from agenticLLM.ports.drivens.forOperationalMemory import ForOperationalMemoryRepository
from agenticLLM.ports.drivens.forSkills import ForSkillRegistry

from agenticLLM.core.agent_logger import get_logger

class AgentUseCase(ForAgentInteraction):
    def __init__(self, llm: ForLLMProvider, tools: ForToolExecution, memory_repo: ForOperationalMemoryRepository, skills: ForSkillRegistry, config: AgentConfig = None):
        self.logger = get_logger()
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
        self.logger.info(f"Agent initialized with persona: {self.config.system_prompt[:50]}...")

    def ask(self, user_input: str) -> str:
        self.logger.info(f"Agent received query: {user_input}")
        # Clear any old pending action
        self.state.pending_action = None
        
        # 1. RAG Step: Retrieve relevant memories
        try:
            relevant_memories = self.memory_repo.search_memories(user_input)
            if relevant_memories:
                self.logger.debug(f"RAG found {len(relevant_memories)} relevant context entries")
                context_str = "\n".join([f"- {m.content}" for m in relevant_memories])
                rag_message = f"Relevant operational context found:\n{context_str}\n\nUse this information to answer the user query: {user_input}"
                self.state.history.append(Message(role="user", content=rag_message))
            else:
                self.state.history.append(Message(role="user", content=user_input))
        except Exception as e:
            self.logger.warning(f"RAG search failed: {e}")
            self.state.history.append(Message(role="user", content=user_input))
        
        return self._run_loop()

    def _run_loop(self) -> str:
        max_iterations = 8 # Increased slightly
        for i in range(max_iterations):
            self.logger.debug(f"Loop iteration {i+1}/{max_iterations}")
            # Refresh available tools from executor to include any tools created during the session
            self.state.available_tools = self.tools_executor.list_tools()

            # 1. Get response from LLM
            assistant_msg = self.llm.generate_response(self.state.history, self.state.available_tools)
            
            # Critical: Ensure we have content if it's not a tool call
            if not assistant_msg.content and not assistant_msg.tool_call_id:
                self.logger.warning("LLM returned empty response")
                return "Agent returned an empty response. Please try rephrasing your request."

            self.state.history.append(assistant_msg)
            
            # 2. Check if it's a tool call
            if not assistant_msg.tool_call_id:
                self.logger.info(f"Agent finished reasoning: {assistant_msg.content[:50]}...")
                return assistant_msg.content
            
            # 3. Find the tool to see if it requires approval
            tool_name = assistant_msg.name or ""
            self.logger.info(f"Agent wants to call tool: {tool_name}")
            target_tool = next((t for t in self.state.available_tools if t.name == tool_name), None)
            
            # Get arguments from new field or fallback to content
            arguments = assistant_msg.tool_arguments or {}
            if not arguments and assistant_msg.content:
                try:
                    # Clean content from possible thinking tags for parsing
                    clean_content = assistant_msg.content
                    if "<think>" in clean_content and "</think>" in clean_content:
                        clean_content = clean_content.split("</think>")[-1].strip()
                    arguments = json.loads(clean_content)
                except:
                    pass

            # Check for duplicate identical tool calls to avoid infinite loops
            if len(self.state.history) > 3:
                last_tool_msgs = [m for m in self.state.history[-6:-1] if m.role == "assistant" and m.tool_call_id]
                for prev in last_tool_msgs:
                    if prev.name == tool_name and prev.tool_arguments == arguments:
                         self.logger.warning(f"Loop detected for tool {tool_name}")
                         return f"Agent is repeating tool call '{tool_name}' with same arguments. Stopping loop."

            if target_tool and target_tool.requires_approval:
                self.logger.info(f"Tool {tool_name} requires operator approval")
                self.state.pending_action = PendingAction(
                    tool_call_id=assistant_msg.tool_call_id,
                    tool_name=tool_name,
                    arguments=arguments
                )
                return f"[WAITING_FOR_APPROVAL]: The agent wants to execute {tool_name}. Do you allow it?"

            # 4. Execute tool directly if no approval required
            self.logger.info(f"Executing tool {tool_name} (No approval needed)")
            result = self.tools_executor.execute_tool(tool_name, arguments)
            self.state.history.append(Message(role="tool", content=result, tool_call_id=assistant_msg.tool_call_id, name=tool_name))
            
        self.logger.error("Max iterations reached in agent loop")
        return "Max iterations (8) reached. The agent might be in a complex loop or failing to conclude. Check tool outputs in history."

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
        self.logger.info(f"User approval for tool {action.tool_name}: {approved}")
        
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
