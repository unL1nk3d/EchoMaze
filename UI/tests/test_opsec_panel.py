"""
UI/tests/test_opsec_panel.py
Unit tests for OpSecPanel widget.

Updated to work with the new Observer-based OpSecPanel API.
Uses __new__ to bypass Frame.__init__ (avoids asciimatics Screen dependency)
while testing the panel's logic in isolation.
"""

import unittest
from unittest.mock import MagicMock
from UI.opsec_panel import OpSecPanel


def _make_panel(noise_score=0, pivot_path=None, service=None):
    """Factory: create an OpSecPanel without invoking Frame.__init__.
    This avoids the need for a real asciimatics Screen with colours/unicode_aware.
    """
    panel = OpSecPanel.__new__(OpSecPanel)
    panel.noise_score = noise_score
    panel.pivot_path = pivot_path or []
    panel.service = service
    panel._state = "ok"
    panel._pending_update = False
    panel._debounce_timer = None
    panel._last_render_data = None
    panel.opsec = MagicMock()
    panel.suggestions_label = MagicMock()
    panel._redraw = MagicMock()
    panel.model = MagicMock()
    return panel


class TestOpSecPanel(unittest.TestCase):

    def setUp(self):
        self.panel = _make_panel(
            noise_score=30,
            pivot_path=["10.0.0.1", "10.0.0.2"],
            service="smb"
        )
        # Configure opsec hooks to return realistic data
        self.panel.opsec.on_noise_score_update.return_value = "Stealth optimal — noise at 30"
        self.panel.opsec.on_pivot_path_change.return_value = [
            "pivot chain: 10.0.0.1 -> 10.0.0.2"
        ]
        self.panel.opsec.on_service_selected.return_value = [
            "smb: consider using named pipes for lateral movement"
        ]

    def test_initial_suggestions_render(self):
        """_render_suggestions should compose tips from hooks."""
        self.panel._render_suggestions()
        text = self.panel.suggestions_label.text
        self.assertIn("Stealth optimal", text)
        self.assertIn("pivot chain", text.lower())
        self.assertIn("smb", text.lower())

    def test_update_panel_changes_suggestions(self):
        """Legacy update_panel should update state and re-render."""
        self.panel.opsec.on_noise_score_update.return_value = "Critical exposure — noise at 80"
        self.panel.opsec.on_pivot_path_change.return_value = []
        self.panel.opsec.on_service_selected.return_value = [
            "rdp: avoid unless necessary"
        ]
        self.panel.update_panel(noise_score=80, pivot_path=[], service="rdp")
        text = self.panel.suggestions_label.text
        self.assertIn("Critical exposure", text)
        self.assertIn("rdp", text.lower())

    def test_update_panel_no_tips(self):
        """When all inputs are None/empty, show 'no suggestions' message."""
        self.panel.opsec.on_noise_score_update.return_value = ""
        self.panel.opsec.on_pivot_path_change.return_value = []
        self.panel.opsec.on_service_selected.return_value = []
        self.panel.update_panel(noise_score=None, pivot_path=None, service=None)
        self.assertIn("No current OpSec suggestions", self.panel.suggestions_label.text)

    def test_observer_update_is_callable(self):
        """OpSecPanel must expose observer_update for the Observer pattern."""
        self.assertTrue(callable(getattr(self.panel, 'observer_update', None)))

    def test_refresh_is_callable(self):
        """OpSecPanel must expose refresh for manual re-fetch."""
        self.assertTrue(callable(getattr(self.panel, 'refresh', None)))


if __name__ == '__main__':
    unittest.main()
