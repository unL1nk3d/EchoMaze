"""
UI/frames/admin_dashboard.py
Dashboard for administrators to view operator actions and OPSEC levels.
"""

from asciimatics.widgets import Frame, Layout, Label, ListBox, Divider, TextBox, Widget
from asciimatics.screen import Screen
from asciimatics.exceptions import NextScene
from UI.models import inject_risk_palette, risk_colour_key_for_score

class AdminDashboardFrame(Frame):
    def __init__(self, screen, model):
        super(AdminDashboardFrame, self).__init__(
            screen,
            screen.height,
            screen.width,
            has_border=True,
            name="Admin Dashboard",
            title="Administrator Dashboard - Operator OPSEC Overview"
        )
        self.model = model
        inject_risk_palette(self.palette)
        
        # Internal state
        self._operator_data = {}
        
        # Layout
        layout = Layout([1, 2], fill_frame=True)
        self.add_layout(layout)
        
        # Column 0: Operator List
        layout.add_widget(Label("Operators"), 0)
        self.operator_list = ListBox(
            height=Widget.FILL_COLUMN,
            options=[],
            name="operator_list",
            on_change=self._on_operator_change
        )
        layout.add_widget(self.operator_list, 0)
        
        # Column 1: Details
        layout.add_widget(Label("Operator Summary"), 1)
        self.summary_text = TextBox(5, as_string=True, line_wrap=True)
        self.summary_text.disabled = True
        layout.add_widget(self.summary_text, 1)
        
        layout.add_widget(Divider(), 1)
        layout.add_widget(Label("Recent Actions"), 1)
        self.actions_list = ListBox(
            height=Widget.FILL_COLUMN,
            options=[],
            name="actions_list"
        )
        layout.add_widget(self.actions_list, 1)
        
        # Footer
        footer_layout = Layout([1])
        self.add_layout(footer_layout)
        footer_layout.add_widget(Divider())
        footer_layout.add_widget(Label("Press 'B' to go back to Tree View"))
        
        self.fix()
        self.refresh_data()

    def reset(self):
        super(AdminDashboardFrame, self).reset()
        if not self.model.is_admin:
            raise NextScene("main")
        self.refresh_data()

    def refresh_data(self):
        """Fetch fresh data from model and update the view."""
        self._operator_data = self.model.get_operator_summary()
        options = []
        for i, (op, data) in enumerate(self._operator_data.items()):
            # Use color indicators in the list
            risk = risk_colour_key_for_score(data['avg_noise'])
            risk_icon = {'risk_green': '', 'risk_yellow': '!', 'risk_red': '!!'}.get(risk, '')
            options.append((f"{op} ({data['count']} acts){risk_icon}", op))
        
        self.operator_list.options = options
        if options:
            self.operator_list.value = options[0][1]
            self._on_operator_change()

    def _on_operator_change(self):
        """Update the details when a different operator is selected."""
        op = self.operator_list.value
        if op and op in self._operator_data:
            data = self._operator_data[op]
            summary = (
                f"Operator: {op}\n"
                f"Total Actions: {data['count']}\n"
                f"Average Noise Score: {data['avg_noise']:.2f}\n"
                f"OPSEC Status: {self._get_opsec_status(data['avg_noise'])}"
            )
            self.summary_text.value = summary
            
            # Update actions list
            action_options = []
            for i, act in enumerate(reversed(data['actions'][-20:])): # Show last 20
                action_options.append((f"[{act.timestamp}] {act.command_template} (Noise: {act.noise_score:.1f})", i))
            self.actions_list.options = action_options
        else:
            self.summary_text.value = ""
            self.actions_list.options = []

    def _get_opsec_status(self, avg_noise):
        if avg_noise >= 65: return "CRITICAL - High Visibility"
        if avg_noise >= 20: return "CAUTION - Moderate Noise"
        return "GOOD - Stealthy"

    def process_event(self, event):
        if hasattr(event, "key_code"):
            if event.key_code in [ord('B'), ord('b')]:
                raise NextScene("main")
            elif event.key_code in [ord('R'), ord('r')]:
                self.refresh_data()
        return super(AdminDashboardFrame, self).process_event(event)
