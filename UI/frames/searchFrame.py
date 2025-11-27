
from asciimatics.widgets import Frame, Layout, Label, ListBox, Divider,TextBox
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import StopApplication, NextScene
from asciimatics.scene import Scene

class SearchFrame(Frame):
    def __init__(self, screen,model):
        super(SearchFrame, self).__init__(screen, screen.height, screen.width, has_border=True, name="Search")
        self.search_text = ""
        self.model = model
        self.filtered_protocols = model.protocols.copy()

        layout = Layout([1])
        self.add_layout(layout)
        layout.add_widget(Label("Buscar IP:"))
        self.search_box = TextBox(1, name="search", on_change=self._on_search_change)
        layout.add_widget(self.search_box)
        layout.add_widget(Divider())

        self.result_list = ListBox(
            height=screen.height - 6,
            options=[(p, i) for i, p in enumerate(self.filtered_protocols)],
            name="results",
            add_scroll_bar=True
        )
        layout.add_widget(self.result_list)
        layout.add_widget(Label("Presiona Q para salir"))
        self.fix()

    def _on_search_change(self):
        self.search_text = self.search_box.value.lower()
        self.filtered_protocols = [p for p in protocols if self.search_text in p.lower()]
        self.result_list.options = [(p, i) for i, p in enumerate(self.filtered_protocols)]

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('Q'), ord('q')]:
                raise NextScene("main")
            if event.key_code in [ord('e'),ord('E')]:  # ESC key
                raise StopApplication("exit")
        return super(SearchFrame, self).process_event(event)