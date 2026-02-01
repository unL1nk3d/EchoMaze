from asciimatics.widgets import Frame, ListBox, Layout, Button, Text, Label
from asciimatics.scene import Scene
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
import pyperclip

class SuggestionsFrame(Frame):
    def __init__(self, screen, model):
        super().__init__(screen,
                         screen.height * 2 // 3,
                         screen.width * 2 // 3,
                         title="Pivoting Suggestions",
                         can_scroll=False,
                         reduce_cpu=True)
        self.model = model
        self.suggestions = []
        self.selected_suggestion = None
        self._load_suggestions()

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)

        self.list_box = ListBox(
            height=10,
            options=[(f"{s.desc} (Noise: {s.noise_estimate})", s) if not s.generic else (f"{s.desc} (Noise: {s.noise_estimate}) <<Generic>>", s) for s in self.suggestions],
            
            name="suggestions",
            on_change=self._on_select
        )
        layout.add_widget(self.list_box)

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Copy Linux", self._copy_linux), 0)
        layout2.add_widget(Button("Copy Windows", self._copy_windows), 1)
        layout2.add_widget(Button("Close", self._close), 2)

        self.fix()

    def _load_suggestions(self):
        if self.model.selected_ip:
            suggestions = self.model.get_suggestions_for_ip(self.model.selected_ip)
            if not suggestions:
                suggestions = self.model.get_generic_suggestions_for_ip(self.model.selected_ip)
                [x.set_generic_flag() for x in suggestions]
            self.suggestions = suggestions

    def _on_select(self):
        self.selected_suggestion = self.list_box.value

    def _copy_linux(self):
        if self.selected_suggestion and hasattr(self.selected_suggestion, 'linux'):
            self.model.copy_to_clipboard(self.selected_suggestion.linux)

    def _copy_windows(self):
        if self.selected_suggestion and hasattr(self.selected_suggestion, 'windows'):
            self.model.copy_to_clipboard(self.selected_suggestion.windows)

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene('main')