"""
UI/frames/artifacts_frame.py
Frame for managing artifacts associated with an IP.
"""

from asciimatics.widgets import Frame, Layout, Label, ListBox, Divider, Text, Widget, Button, PopUpDialog
from asciimatics.exceptions import NextScene
from UI.models import inject_risk_palette

class ArtifactsFrame(Frame):
    def __init__(self, screen, model):
        super(ArtifactsFrame, self).__init__(
            screen,
            screen.height,
            screen.width,
            has_border=True,
            name="Artifacts Manager",
            title="Artifacts Management"
        )
        self.model = model
        inject_risk_palette(self.palette)
        
        # Layout
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        
        # Left column: List of artifacts
        layout.add_widget(Label("Artifacts for selected IP"), 0)
        self.artifacts_list = ListBox(
            height=Widget.FILL_COLUMN,
            options=[],
            name="artifacts_list"
        )
        layout.add_widget(self.artifacts_list, 0)
        
        # Right column: Add new artifact
        layout.add_widget(Label("Add New Artifact"), 1)
        self.filename = Text("Filename:", name="filename")
        self.notes = Text("Notes:", name="notes")
        self.noise_score = Text("Noise Score (empty for default):", name="noise_score")
        
        layout.add_widget(self.filename, 1)
        layout.add_widget(self.notes, 1)
        layout.add_widget(self.noise_score, 1)
        
        button_layout = Layout([1, 1])
        self.add_layout(button_layout)
        button_layout.add_widget(Button("Add", self._add_artifact), 0)
        button_layout.add_widget(Button("Back", self._back), 1)
        
        self.fix()
        self.refresh_data()

    def reset(self):
        super(ArtifactsFrame, self).reset()
        self.refresh_data()

    def refresh_data(self):
        ip = self.model.selected_ip
        if not ip:
            self.artifacts_list.options = [("No IP selected", 0)]
            return
        
        artifacts = self.model.get_artifacts_for_ip(ip)
        options = []
        for i, art in enumerate(artifacts):
            options.append((f"{art.filename} - {art.notes} (Noise: {art.noise_score})", i))
        
        if not options:
            options = [("No artifacts found", 0)]
        self.artifacts_list.options = options

    def _add_artifact(self):
        filename = self.filename.value
        notes = self.notes.value
        noise_str = self.noise_score.value
        ip = self.model.selected_ip
        
        if not filename or not ip:
            self._scene.add_effect(PopUpDialog(self._screen, "Filename and selected IP are required!", ["OK"]))
            return
        
        try:
            noise = float(noise_str) if noise_str else None
        except ValueError:
            self._scene.add_effect(PopUpDialog(self._screen, "Noise Score must be a number!", ["OK"]))
            return

        success = self.model.add_artifact(ip, filename, notes, noise)
        if success:
            self.filename.value = ""
            self.notes.value = ""
            self.noise_score.value = ""
            self.refresh_data()
            self._scene.add_effect(PopUpDialog(self._screen, "Artifact added and OPSEC updated!", ["OK"]))
        else:
            self._scene.add_effect(PopUpDialog(self._screen, "Failed to add artifact.", ["OK"]))

    def _back(self):
        raise NextScene("main")

    def process_event(self, event):
        if hasattr(event, "key_code"):
            if event.key_code in [ord('B'), ord('b')]:
                self._back()
        return super(ArtifactsFrame, self).process_event(event)
