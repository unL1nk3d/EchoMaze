from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text, PopUpDialog, Widget, Divider, DropdownList, CheckBox
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from agenticLLM.models.agent import Message
import threading

class AgentDashboardFrame(Frame):
    def __init__(self, screen: Screen, model):
        super(AgentDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="EchoMaze AI Agent",
            can_scroll=True,
            reduce_cpu=False # Allow continuous background update for thinking
        )
        self.model = model
        self.agent = model.agent_usecase
        self.manager = model.agent_manager
        self._active_agent_name = "default"
        self._is_thinking = False
        self._pending_response = None
        self._thinking_animation_count = 0

        self.history_text = TextBox(height=13, label="Conversation:", name="history", as_string=True, line_wrap=True)
        self.history_text.readonly = True
        
        self.input_text = Text(label="Ask AI:", name="user_input")
        
        # Model & Agent Configuration Widgets
        self.agent_dropdown = DropdownList(
            [("Default", "default")],
            label="Active Agent:",
            name="active_agent",
            on_change=self._on_agent_change
        )
        self.model_dropdown = DropdownList(
            [("Default", "default")],
            label="Ollama Model:",
            name="ollama_model",
            on_change=self._on_model_change
        )
        self.react_checkbox = CheckBox("Use ReAct Mode", name="use_react", on_change=self._on_react_change)
        
        self._rebuild_layout()
        self._refresh_agent_list()
        self._refresh_agent_info()
        self._refresh_history()
        self._load_available_models()

    def _refresh_agent_list(self):
        if not self.manager:
            return

        # Dynamically discover all possible personas from PromptManager
        all_personas = self.manager.prompt_manager.list_keys()
        
        # Ensure all discovered specialized personas are registered in the manager
        # (excluding 'default' which is handled specially)
        for persona in all_personas:
            if persona != "default" and persona not in self.manager.list_agents():
                self.manager.create_agent(persona, persona=persona)
        
        # Get the full list of active agent sessions
        agents = self.manager.list_agents()
        options = [(a.upper(), a) for a in agents]
        self.agent_dropdown.options = options
        self.agent_dropdown.value = self._active_agent_name

    def _on_agent_change(self):
        self.save()
        new_agent = self.data.get("active_agent")
        if not new_agent or new_agent == self._active_agent_name:
            return
            
        self._active_agent_name = new_agent
        self.agent = self.manager.get_agent(self._active_agent_name)
        self.model.agent_usecase = self.agent
        
        self._refresh_agent_info()
        self._refresh_history()
        self._load_available_models()

    def _refresh_agent_info(self):
        # Update title to show which agent is active
        self._title = f"EchoMaze AI Agent [{self._active_agent_name.upper()}]"

    def _rebuild_layout(self):
        self._layouts = []
        
        layout_config = Layout([35, 35, 30])
        self.add_layout(layout_config)
        layout_config.add_widget(self.agent_dropdown, 0)
        layout_config.add_widget(self.model_dropdown, 1)
        layout_config.add_widget(self.react_checkbox, 2)
        layout_config.add_widget(Divider(), 0)
        layout_config.add_widget(Divider(), 1)
        layout_config.add_widget(Divider(), 2)

        layout_history = Layout([100])
        self.add_layout(layout_history)
        layout_history.add_widget(self.history_text)
        layout_history.add_widget(Divider())

        layout_input = Layout([80, 20])
        self.add_layout(layout_input)
        layout_input.add_widget(self.input_text, 0)
        layout_input.add_widget(Button("Send", self._send_query), 1)

        layout_buttons = Layout([1, 1, 1])
        self.add_layout(layout_buttons)
        layout_buttons.add_widget(Button("Compact", self._compact_history), 0)
        layout_buttons.add_widget(Button("Reset", self._reset_agent), 1)
        layout_buttons.add_widget(Button("Close", self._close), 2)

        self.fix()

    def _compact_history(self):
        if self._is_thinking: return

        self._is_thinking = True
        self.history_text.value += "[System]: Generating summary and compacting history...\n\n"

        def _background_compact():
            try:
                resp = self.agent.compact_history()
                self._pending_response = resp
            except Exception as e:
                self._pending_response = f"Error during compaction: {str(e)}"

        threading.Thread(target=_background_compact, daemon=True).start()

    def _load_available_models(self):
        # Only relevant for Ollama
        from agenticLLM.adapters.drivens.OllamaAdapter import OllamaAdapter
        
        # We need to find the actual OllamaAdapter if it's wrapped or in the chain
        adapter = self.agent.llm
        while hasattr(adapter, 'inner_provider'):
             adapter = adapter.inner_provider
             
        if isinstance(adapter, OllamaAdapter):
            models = adapter.list_available_models()
            if models:
                options = [(m, m) for m in models]
                self.model_dropdown.options = options
                # Select current model if possible
                if adapter.model_name in models:
                    self.model_dropdown.value = adapter.model_name
            
            # Sync ReAct checkbox
            main_adapter = self.agent.llm
            self.react_checkbox.value = getattr(main_adapter, 'use_react', False)

    def _on_model_change(self):
        self.save()
        new_model = self.data.get("ollama_model")
        if not new_model: return
        
        from agenticLLM.adapters.drivens.OllamaAdapter import OllamaAdapter
        adapter = self.agent.llm
        while hasattr(adapter, 'inner_provider'):
             adapter = adapter.inner_provider
             
        if isinstance(adapter, OllamaAdapter):
            adapter.model_name = new_model

    def _on_react_change(self):
        self.save()
        use_react = self.data.get("use_react")
        
        # Update the adapter
        adapter = self.agent.llm
        if hasattr(adapter, 'use_react'):
            adapter.use_react = use_react

    def update(self, frame_no):
        # Polling check for background response
        if self._is_thinking and self._pending_response is not None:
            response = self._pending_response
            self._pending_response = None
            self._is_thinking = False
            
            if "[WAITING_FOR_APPROVAL]" in response:
                self._ask_for_approval()
            
            self._refresh_history()
            
        super(AgentDashboardFrame, self).update(frame_no)

    def process_event(self, event):
        return super(AgentDashboardFrame, self).process_event(event)

    def _send_query(self):
        if self._is_thinking:
            return

        self.save()
        user_query = self.data.get("user_input")
        if user_query:
            self.input_text.value = ""
            
            # Intercept special query commands
            if user_query.strip().startswith("?"):
                self._handle_special_command(user_query.strip())
                self._refresh_history()
                return

            # Start thinking in background
            self._is_thinking = True
            self._pending_response = None
            
            # Add a placeholder for "thinking"
            self.agent.state.history.append(Message(role="user", content=user_query))
            self._refresh_history()
            self.history_text.value += "[EchoAI]: Thinking...\n\n"

            def _background_ask():
                try:
                    # Note: We skip the first ask() logic here because we already added the user message
                    # and we don't want to duplicate RAG logic. 
                    # But actually, ask() handles RAG and history. Let's use ask() but revert the manual append.
                    self.agent.state.history.pop() 
                    response = self.agent.ask(user_query)
                    self._pending_response = response
                except Exception as e:
                    self._pending_response = f"Error: {str(e)}"

            threading.Thread(target=_background_ask, daemon=True).start()
        else:
            self._scene.add_effect(PopUpDialog(self._screen, "Please enter a query", ["OK"]))

    def _handle_special_command(self, cmd: str):
        if cmd == "?skills":
            skills = self.agent.skills_registry.list_available_skills()
            output = "AVAILABLE SKILLS:\n"
            for s in skills:
                output += f"- {s.name}: {s.description}\n"
            self.agent.state.history.append(Message(role="user", content="[CMD] ?skills"))
            self.agent.state.history.append(Message(role="assistant", content=output))
            
        elif cmd == "?memories":
            memories = self.agent.memory_repo.list_all_memories()
            output = "OPERATIONAL MEMORIES (RAG):\n"
            for m in memories:
                output += f"- [{m.timestamp}] {m.content}\n"
            if not memories: output += "(No memories stored yet)"
            self.agent.state.history.append(Message(role="user", content="[CMD] ?memories"))
            self.agent.state.history.append(Message(role="assistant", content=output))
        
        elif cmd == "?tools":
            tools = self.agent.tools_executor.list_tools()
            output = "AVAILABLE SYSTEM TOOLS:\n"
            for t in tools:
                output += f"- {t.name}: {t.description}\n"
            self.agent.state.history.append(Message(role="user", content="[CMD] ?tools"))
            self.agent.state.history.append(Message(role="assistant", content=output))
        
        else:
            self._scene.add_effect(PopUpDialog(self._screen, f"Unknown command: {cmd}", ["OK"]))

    def _ask_for_approval(self):
        pending = self.agent.get_pending_action()
        if not pending: return
        
        msg = f"APPROVAL REQUIRED\n\nTool: {pending['tool_name']}\nArgs: {pending['arguments']}\n\nDo you want to allow this action?"
        
        def _on_approve():
            self._is_thinking = True
            self.history_text.value += "[EchoAI]: Executing tool and thinking...\n\n"
            def _background_approve():
                try:
                    resp = self.agent.provide_approval(True)
                    self._pending_response = resp
                except Exception as e:
                    self._pending_response = f"Error: {str(e)}"
            threading.Thread(target=_background_approve, daemon=True).start()

        def _on_reject():
            self._is_thinking = True
            self.history_text.value += "[EchoAI]: Action rejected, thinking...\n\n"
            def _background_reject():
                try:
                    resp = self.agent.provide_approval(False)
                    self._pending_response = resp
                except Exception as e:
                    self._pending_response = f"Error: {str(e)}"
            threading.Thread(target=_background_reject, daemon=True).start()

        self._scene.add_effect(PopUpDialog(
            self._screen, 
            msg, 
            [("Approve", _on_approve), ("Reject", _on_reject)]
        ))

    def _reset_agent(self):
        self.agent.reset()
        self._refresh_history()
        self._scene.add_effect(PopUpDialog(self._screen, "Agent history cleared", ["OK"]))

    def _refresh_history(self):
        history = self.agent.get_history()
        formatted_history = ""
        for msg in history:
            if msg.role == "system": continue
            
            if msg.role == "user":
                role_label = "Operator"
                content = msg.content
            elif msg.role == "tool":
                role_label = f"Tool Result ({msg.name})"
                content = msg.content
            else:
                role_label = "EchoAI"
                content = msg.content
                # Handle thinking tags if present
                if "<think>" in content and "</think>" in content:
                    parts = content.split("</think>")
                    thought = parts[0].replace("<think>", "").strip()
                    answer = parts[1].strip()
                    content = f"[Reasoning]: {thought}\n\n[Answer]: {answer}"
                
            formatted_history += f"[{role_label}]: {content}\n\n"
        
        self.history_text.value = formatted_history

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("main")
