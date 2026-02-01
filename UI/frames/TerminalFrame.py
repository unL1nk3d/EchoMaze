from asciimatics.widgets import Frame, Layout, Text, Button, MultiColumnListBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import NextScene
import subprocess
import threading

class TerminalFrame(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height * 2 // 3,
                         screen.width * 2 // 3,
                         title="Integrated Terminal",
                         can_scroll=False,
                         reduce_cpu=True)
        self.model = model
        self.history = []
        self.current_command = ""

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)

        self.output_list = MultiColumnListBox(
            height=10,
            columns=[0, 0],
            options=[],
            name="output"
        )
        layout.add_widget(self.output_list)

        self.command_input = Text(name="command", on_change=self._on_command_change)
        layout.add_widget(self.command_input)

        layout2 = Layout([1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Execute", self._execute_command), 0)
        layout2.add_widget(Button("Close", self._close), 1)

        self.fix()

    def _on_command_change(self):
        self.current_command = self.command_input.value

    def _execute_command(self):
        if self.current_command:
            def run_command():
                try:
                    result = subprocess.run(self.current_command, shell=True, capture_output=True, text=True)
                    output = result.stdout + result.stderr
                    self.history.append((self.current_command, output))
                    self._update_output()
                except Exception as e:
                    self.history.append((self.current_command, str(e)))
                    self._update_output()
            threading.Thread(target=run_command).start()

    def _update_output(self):
        options = [(cmd, out, i) for i, (cmd, out) in enumerate(self.history)]
        self.output_list.options = options
        self.output_list.value = len(options) - 1

    def _close(self):
        #self._scene.remove_effect(self)
        raise NextScene('main')