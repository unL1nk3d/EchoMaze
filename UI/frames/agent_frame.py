from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text, PopUpDialog, Widget, Divider
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from agenticLLM.models.agent import Message

class AgentDashboardFrame(Frame):
    def __init__(self, screen: Screen, model):
        super(AgentDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="EchoMaze AI Agent",
            can_scroll=True,
            reduce_cpu=True
        )
        self.model = model
        self.agent = model.agent_usecase

        self.history_text = TextBox(height=15, label="Conversation:", name="history", as_string=True, line_wrap=True)
        self.history_text.disabled = True
        
        self.input_text = Text(label="Ask AI:", name="user_input")
        
        self._rebuild_layout()
        self._refresh_history()

    def _rebuild_layout(self):
        self._layouts = []
        
        layout_history = Layout([100])
        self.add_layout(layout_history)
        layout_history.add_widget(self.history_text)
        layout_history.add_widget(Divider())

        layout_input = Layout([80, 20])
        self.add_layout(layout_input)
        layout_input.add_widget(self.input_text, 0)
        layout_input.add_widget(Button("Send", self._send_query), 1)

        layout_buttons = Layout([1, 1])
        self.add_layout(layout_buttons)
        layout_buttons.add_widget(Button("Reset", self._reset_agent), 0)
        layout_buttons.add_widget(Button("Close", self._close), 1)

        self.fix()

    def _send_query(self):
        self.save()
        user_query = self.data.get("user_input")
        if user_query:
            self.input_text.value = ""
            
            # Intercept special query commands
            if user_query.strip().startswith("?"):
                self._handle_special_command(user_query.strip())
                self._refresh_history()
                return

            response = self.agent.ask(user_query)
            
            if "[WAITING_FOR_APPROVAL]" in response:
                self._ask_for_approval()
            
            self._refresh_history()
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
            resp = self.agent.provide_approval(True)
            if "[WAITING_FOR_APPROVAL]" in resp:
                self._ask_for_approval()
            self._refresh_history()

        def _on_reject():
            resp = self.agent.provide_approval(False)
            if "[WAITING_FOR_APPROVAL]" in resp:
                self._ask_for_approval()
            self._refresh_history()

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
            role_label = "Operator" if msg.role == "user" else "EchoAI"
            formatted_history += f"[{role_label}]: {msg.content}\n\n"
        
        self.history_text.value = formatted_history

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("main")
