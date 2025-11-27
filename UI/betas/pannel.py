from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import Frame, Layout, Label, Divider, TextBox
from asciimatics.exceptions import StopApplication
from asciimatics.event import KeyboardEvent

class TogglePanel(Frame):
    def __init__(self, screen):
        super(TogglePanel, self).__init__(screen, screen.height, screen.width, has_border=False, name="Main")
        self.panel_visible = False

        layout = Layout([1])
        self.add_layout(layout)
        layout.add_widget(Label("bg nmap -sS -n -oG inform.txt 192.168.30.2"))
        layout.add_widget(Divider())
        self.panel = TextBox(
            height=4,
            label="",
            name="panel",
            as_string=True,
            line_wrap=True
        )
        self.panel.value = "| ip        | parent_ip |\n|-----------|------------|\n| 192.168.1 | 172.16.1   |"
        self.panel.disabled = True
        layout.add_widget(self.panel)
        #self.panel.

        layout.add_widget(Divider())
        layout.add_widget(Label("echo \"hello\""))

        self.fix()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == -19:  # CTRL + S
                self.panel.show()
                self.panel_visible = True
            elif event.key_code == -3:  # CTRL + C
                self.panel.hide()
                self.panel_visible = False
            elif event.key_code in [ord('Q'), ord('q')]:
                raise StopApplication("Exit")
        return super(TogglePanel, self).process_event(event)

def run(screen):
    scene = Scene([TogglePanel(screen)], -1)
    screen.play([scene], stop_on_resize=True)

Screen.wrapper(run)
