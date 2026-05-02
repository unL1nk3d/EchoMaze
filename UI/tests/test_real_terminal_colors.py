"""
UI/tests/test_real_terminal_colors.py
TDD tests for real terminal color integration in TreeIPFrame and OpSecPanel.

Validates that:
  1. RISK_PALETTE_ENTRIES defines correct color tuples for green/yellow/red
  2. inject_risk_palette() adds risk_* keys to any Frame palette
  3. TreeIPFrame applies custom_colour on details_text and inline_suggestions_label
  4. OpSecPanel applies custom_colour on suggestions_label
  5. risk_colour_key_for_score() maps score → palette key name

Run with:
  python -m unittest UI.tests.test_real_terminal_colors -v
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from collections import defaultdict
from asciimatics.screen import Screen


# ===========================================================================
# Helpers
# ===========================================================================

def _make_model_with_scoring(scoring_engine=None, cachered_ips=None):
    """Create a GenericModel with optional ScoringEngine injection."""
    from UI.models import GenericModel
    repo = MagicMock()
    repo.select_all_ips = MagicMock(return_value=[])
    repo.select_all_ports = MagicMock(return_value=[])
    model = GenericModel(
        repository=repo,
        commands=None,
        scoring_engine=scoring_engine,
    )
    if cachered_ips is not None:
        model._cachered = cachered_ips
    return model


# ===========================================================================
# PHASE 1: RISK_PALETTE_ENTRIES and helpers in UI/models.py
# ===========================================================================

class TestRiskPaletteEntries(unittest.TestCase):
    """RISK_PALETTE_ENTRIES must define colour tuples for green/yellow/red."""

    def test_risk_palette_entries_exists(self):
        """RISK_PALETTE_ENTRIES should be importable from UI.models."""
        from UI.models import RISK_PALETTE_ENTRIES
        self.assertIsInstance(RISK_PALETTE_ENTRIES, dict)

    def test_risk_palette_has_three_keys(self):
        """Must have exactly risk_green, risk_yellow, risk_red."""
        from UI.models import RISK_PALETTE_ENTRIES
        self.assertIn('risk_green', RISK_PALETTE_ENTRIES)
        self.assertIn('risk_yellow', RISK_PALETTE_ENTRIES)
        self.assertIn('risk_red', RISK_PALETTE_ENTRIES)

    def test_risk_green_is_green_foreground(self):
        """risk_green must use Screen.COLOUR_GREEN as foreground."""
        from UI.models import RISK_PALETTE_ENTRIES
        fg, attr, bg = RISK_PALETTE_ENTRIES['risk_green']
        self.assertEqual(fg, Screen.COLOUR_GREEN)

    def test_risk_yellow_is_yellow_foreground(self):
        """risk_yellow must use Screen.COLOUR_YELLOW as foreground."""
        from UI.models import RISK_PALETTE_ENTRIES
        fg, attr, bg = RISK_PALETTE_ENTRIES['risk_yellow']
        self.assertEqual(fg, Screen.COLOUR_YELLOW)

    def test_risk_red_is_red_foreground(self):
        """risk_red must use Screen.COLOUR_RED as foreground."""
        from UI.models import RISK_PALETTE_ENTRIES
        fg, attr, bg = RISK_PALETTE_ENTRIES['risk_red']
        self.assertEqual(fg, Screen.COLOUR_RED)

    def test_each_entry_is_3_tuple(self):
        """Each palette entry must be a 3-tuple (fg, attr, bg)."""
        from UI.models import RISK_PALETTE_ENTRIES
        for key, entry in RISK_PALETTE_ENTRIES.items():
            self.assertEqual(len(entry), 3, f"{key} must be a 3-tuple")


class TestInjectRiskPalette(unittest.TestCase):
    """inject_risk_palette(palette) must add risk_* entries to a palette."""

    def test_inject_risk_palette_function_exists(self):
        """inject_risk_palette should be importable from UI.models."""
        from UI.models import inject_risk_palette
        self.assertTrue(callable(inject_risk_palette))

    def test_inject_adds_risk_keys_to_defaultdict(self):
        """After injection, palette should contain risk_green, risk_yellow, risk_red."""
        from UI.models import inject_risk_palette
        palette = defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        inject_risk_palette(palette)
        self.assertIn('risk_green', palette)
        self.assertIn('risk_yellow', palette)
        self.assertIn('risk_red', palette)

    def test_inject_preserves_existing_keys(self):
        """Injection should not overwrite existing palette keys."""
        from UI.models import inject_risk_palette
        palette = defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))
        original_label = (Screen.COLOUR_CYAN, Screen.A_BOLD, Screen.COLOUR_BLACK)
        palette['label'] = original_label
        inject_risk_palette(palette)
        self.assertEqual(palette['label'], original_label)

    def test_inject_works_with_regular_dict(self):
        """Should work with regular dict too, not just defaultdict."""
        from UI.models import inject_risk_palette
        palette = {}
        inject_risk_palette(palette)
        self.assertIn('risk_green', palette)
        self.assertIn('risk_yellow', palette)
        self.assertIn('risk_red', palette)


class TestRiskColourKeyForScore(unittest.TestCase):
    """risk_colour_key_for_score(score) maps score → palette key name."""

    def test_function_exists(self):
        """risk_colour_key_for_score should be importable from UI.models."""
        from UI.models import risk_colour_key_for_score
        self.assertTrue(callable(risk_colour_key_for_score))

    def test_low_score_returns_risk_green(self):
        """Score below low threshold → 'risk_green'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(5.0), 'risk_green')

    def test_medium_score_returns_risk_yellow(self):
        """Score between thresholds → 'risk_yellow'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(30.0), 'risk_yellow')

    def test_high_score_returns_risk_red(self):
        """Score above high threshold → 'risk_red'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(70.0), 'risk_red')

    def test_zero_returns_risk_green(self):
        """Zero score → 'risk_green'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(0.0), 'risk_green')

    def test_boundary_low_returns_risk_yellow(self):
        """Score exactly at low threshold (20) → 'risk_yellow'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(20.0), 'risk_yellow')

    def test_boundary_high_returns_risk_red(self):
        """Score exactly at high threshold (65) → 'risk_red'."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(65.0), 'risk_red')

    def test_custom_thresholds(self):
        """Custom low/high thresholds should be respected."""
        from UI.models import risk_colour_key_for_score
        self.assertEqual(risk_colour_key_for_score(5.0, low=10, high=50), 'risk_green')
        self.assertEqual(risk_colour_key_for_score(25.0, low=10, high=50), 'risk_yellow')
        self.assertEqual(risk_colour_key_for_score(55.0, low=10, high=50), 'risk_red')


# ===========================================================================
# PHASE 2: TreeIPFrame real colour integration
# ===========================================================================

class TestTreeIPFrameRealColours(unittest.TestCase):
    """TreeIPFrame must inject risk palette and apply custom_colour dynamically."""

    def test_tree_ip_frame_palette_has_risk_entries(self):
        """After construction, TreeIPFrame.palette should contain risk_* keys."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 0.0
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        frame = TreeIPFrame(screen, model)
        # palette should have risk keys injected
        self.assertIn('risk_green', frame.palette)
        self.assertIn('risk_yellow', frame.palette)
        self.assertIn('risk_red', frame.palette)

    def test_details_text_custom_colour_matches_risk_level(self):
        """details_text.custom_colour should be set to the appropriate risk key."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 50.0  # yellow risk
        mock_engine.aggregate_pivot_noise.return_value = {'total_noise': 50.0, 'per_ip': {'10.0.0.1': 50.0}}
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        frame = TreeIPFrame(screen, model)
        # Simulate selecting an IP to trigger _show_node_details
        node = {'ip': '10.0.0.1', 'parent': None, 'protocols': ['ssh'], 'type': 'principal', 'indent': 0}
        frame._show_node_details(node)
        self.assertEqual(frame.details_text.custom_colour, 'risk_yellow')

    def test_details_text_custom_colour_green_for_low_score(self):
        """Low score → details_text.custom_colour = 'risk_green'."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 5.0  # green risk
        mock_engine.aggregate_pivot_noise.return_value = {'total_noise': 5.0, 'per_ip': {'10.0.0.1': 5.0}}
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        frame = TreeIPFrame(screen, model)
        node = {'ip': '10.0.0.1', 'parent': None, 'protocols': ['ssh'], 'type': 'principal', 'indent': 0}
        frame._show_node_details(node)
        self.assertEqual(frame.details_text.custom_colour, 'risk_green')

    def test_details_text_custom_colour_red_for_high_score(self):
        """High score → details_text.custom_colour = 'risk_red'."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 80.0  # red risk
        mock_engine.aggregate_pivot_noise.return_value = {'total_noise': 80.0, 'per_ip': {'10.0.0.1': 80.0}}
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        frame = TreeIPFrame(screen, model)
        node = {'ip': '10.0.0.1', 'parent': None, 'protocols': ['ssh'], 'type': 'principal', 'indent': 0}
        frame._show_node_details(node)
        self.assertEqual(frame.details_text.custom_colour, 'risk_red')

    def test_inline_suggestions_label_gets_custom_colour(self):
        """inline_suggestions_label.custom_colour should be set when updating suggestions."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 50.0  # yellow
        mock_engine.aggregate_pivot_noise.return_value = {'total_noise': 50.0, 'per_ip': {'10.0.0.1': 50.0}}
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        frame = TreeIPFrame(screen, model)
        frame._update_inline_suggestions('10.0.0.1')
        self.assertEqual(frame.inline_suggestions_label.custom_colour, 'risk_yellow')


# ===========================================================================
# PHASE 3: OpSecPanel real colour integration
# ===========================================================================

class TestOpSecPanelRealColours(unittest.TestCase):
    """OpSecPanel must inject risk palette and apply custom_colour on suggestions_label."""

    def test_opsec_panel_palette_has_risk_entries(self):
        """After construction, OpSecPanel.palette should contain risk_* keys."""
        from UI.opsec_panel import OpSecPanel
        model = _make_model_with_scoring(cachered_ips=[])
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        panel = OpSecPanel(screen, model)
        self.assertIn('risk_green', panel.palette)
        self.assertIn('risk_yellow', panel.palette)
        self.assertIn('risk_red', panel.palette)

    def test_suggestions_label_colour_after_score_update(self):
        """When noise_score changes via observer_update, suggestions_label custom_colour should update."""
        from UI.opsec_panel import OpSecPanel
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 70.0
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        panel = OpSecPanel(screen, model, noise_score=70.0)
        # Trigger render with high score
        panel._render_suggestions()
        self.assertEqual(panel.suggestions_label.custom_colour, 'risk_red')

    def test_suggestions_label_colour_green_for_low_score(self):
        """Low noise score → suggestions_label.custom_colour = 'risk_green'."""
        from UI.opsec_panel import OpSecPanel
        model = _make_model_with_scoring(cachered_ips=[])
        screen = MagicMock()
        screen.height = 40
        screen.width = 120
        screen.colours = 256
        screen.unicode_aware = True
        panel = OpSecPanel(screen, model, noise_score=5.0)
        panel._render_suggestions()
        self.assertEqual(panel.suggestions_label.custom_colour, 'risk_green')


if __name__ == '__main__':
    unittest.main()
