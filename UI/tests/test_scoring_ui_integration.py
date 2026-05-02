"""
UI/tests/test_scoring_ui_integration.py
TDD tests for the full Scoring ↔ UI integration cycle:

  PHASE 1: ScoringEngine injection into GenericModel + real get_opsec_data()
  PHASE 2: Aggregate noise by pivot path
  PHASE 3: Risk color mapping (green/yellow/red) for tree nodes + details
  PHASE 4: Tactical suggestions embedded in TreeIPFrame

NOTE: All tests follow RED→GREEN TDD. Run with:
  python -m unittest UI.tests.test_scoring_ui_integration -v
"""

import unittest
import time
from unittest.mock import MagicMock, patch, PropertyMock


# ===========================================================================
# Helpers
# ===========================================================================

def _make_mock_crud():
    """Create a mock CRUD with standard DAO interface."""
    crud = MagicMock()
    crud.dao = MagicMock()
    return crud


def _make_ip_node(ip, parent_ip='', child_level=0, score=0.0, opsec_flag=0, node_id=1):
    """Create a mock IPNode."""
    node = MagicMock()
    node.id = node_id
    node.ip = ip
    node.path = ''
    node.parent_ip = parent_ip
    node.child_level = child_level
    node.score = score
    node.opsec_flag = opsec_flag
    return node


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
# PHASE 1: ScoringEngine injection into GenericModel
# ===========================================================================

class TestScoringEngineInjection(unittest.TestCase):
    """GenericModel must accept an optional scoring_engine parameter."""

    def test_generic_model_accepts_scoring_engine_kwarg(self):
        """GenericModel.__init__ should accept scoring_engine=... without error."""
        mock_engine = MagicMock()
        model = _make_model_with_scoring(scoring_engine=mock_engine)
        self.assertIs(model.scoring_engine, mock_engine)

    def test_generic_model_scoring_engine_defaults_to_none(self):
        """When no scoring_engine is provided, it should be None."""
        model = _make_model_with_scoring(scoring_engine=None)
        self.assertIsNone(model.scoring_engine)

    def test_get_opsec_data_uses_scoring_engine_for_noise_score(self):
        """get_opsec_data should query ScoringEngine.get_score(ip) for real noise."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 42.5
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        mock_engine.get_score.assert_called_once_with('10.0.0.1')
        self.assertEqual(result['noise_score'], 42.5)

    def test_get_opsec_data_returns_zero_without_scoring_engine(self):
        """Without a scoring engine, noise_score should be 0."""
        model = _make_model_with_scoring(
            scoring_engine=None,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertEqual(result['noise_score'], 0)

    def test_get_opsec_data_returns_correct_service(self):
        """get_opsec_data should return the first service for the IP."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 10.0
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['http', 'ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertEqual(result['service'], 'http')


class TestPivotPathFromHierarchy(unittest.TestCase):
    """GenericModel.get_opsec_data() must build pivot_path from parent_ip chain."""

    def test_root_ip_has_single_element_pivot_path(self):
        """A root IP (child_level=0, no parent) should have pivot_path=[ip]."""
        model = _make_model_with_scoring(
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertEqual(result['pivot_path'], ['10.0.0.1'])

    def test_child_ip_has_two_element_pivot_path(self):
        """A child IP should include its parent in the pivot_path."""
        model = _make_model_with_scoring(
            cachered_ips=[
                ('10.0.0.1', '', ['ssh'], 0),
                ('10.0.0.50', '10.0.0.1', ['ldap'], 1),
            ]
        )
        result = model.get_opsec_data('10.0.0.50')
        self.assertEqual(result['pivot_path'], ['10.0.0.1', '10.0.0.50'])

    def test_deep_child_has_full_pivot_chain(self):
        """A deeply nested IP should include the full parent chain."""
        model = _make_model_with_scoring(
            cachered_ips=[
                ('10.0.0.1', '', ['ssh'], 0),
                ('10.0.0.50', '10.0.0.1', ['ldap'], 1),
                ('10.0.0.99', '10.0.0.50', ['redis'], 2),
            ]
        )
        result = model.get_opsec_data('10.0.0.99')
        self.assertEqual(result['pivot_path'], ['10.0.0.1', '10.0.0.50', '10.0.0.99'])

    def test_unknown_ip_returns_empty_pivot_path(self):
        """An IP not in cachered_ips should return empty pivot_path."""
        model = _make_model_with_scoring(
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('99.99.99.99')
        self.assertEqual(result['pivot_path'], [])

    def test_pivot_path_order_is_root_to_leaf(self):
        """Pivot path must be ordered root → ... → leaf (not reversed)."""
        model = _make_model_with_scoring(
            cachered_ips=[
                ('192.168.1.1', '', ['http'], 0),
                ('192.168.1.100', '192.168.1.1', ['mysql'], 1),
                ('192.168.1.200', '192.168.1.100', ['redis'], 2),
                ('192.168.1.250', '192.168.1.200', ['ssh'], 3),
            ]
        )
        result = model.get_opsec_data('192.168.1.250')
        self.assertEqual(result['pivot_path'], [
            '192.168.1.1', '192.168.1.100', '192.168.1.200', '192.168.1.250'
        ])


# ===========================================================================
# PHASE 2: Aggregate noise by pivot path
# ===========================================================================

class TestAggregatePivotNoise(unittest.TestCase):
    """ScoringEngine must calculate aggregate noise across a pivot path."""

    def test_aggregate_pivot_noise_method_exists(self):
        """ScoringEngine should have an aggregate_pivot_noise(path) method."""
        from core.scoring import ScoringEngine
        crud = _make_mock_crud()
        engine = ScoringEngine(crud=crud)
        self.assertTrue(hasattr(engine, 'aggregate_pivot_noise'))

    def test_aggregate_pivot_noise_single_ip(self):
        """Single IP path: aggregate = that IP's score."""
        from core.scoring import ScoringEngine
        crud = _make_mock_crud()
        node = _make_ip_node('10.0.0.1', score=15.0)
        crud.select_ip_by_field.return_value = [node]

        engine = ScoringEngine(crud=crud)
        result = engine.aggregate_pivot_noise(['10.0.0.1'])
        self.assertEqual(result['total_noise'], 15.0)
        self.assertEqual(len(result['per_ip']), 1)
        self.assertEqual(result['per_ip']['10.0.0.1'], 15.0)

    def test_aggregate_pivot_noise_multiple_ips(self):
        """Multiple IP path: aggregate = sum of all scores."""
        from core.scoring import ScoringEngine
        crud = _make_mock_crud()

        nodes = {
            '10.0.0.1': _make_ip_node('10.0.0.1', score=10.0, node_id=1),
            '10.0.0.50': _make_ip_node('10.0.0.50', score=25.0, node_id=2),
            '10.0.0.99': _make_ip_node('10.0.0.99', score=5.0, node_id=3),
        }
        crud.select_ip_by_field.side_effect = lambda field, ip, dao: [nodes[ip]] if ip in nodes else []

        engine = ScoringEngine(crud=crud)
        result = engine.aggregate_pivot_noise(['10.0.0.1', '10.0.0.50', '10.0.0.99'])
        self.assertEqual(result['total_noise'], 40.0)
        self.assertEqual(result['per_ip']['10.0.0.1'], 10.0)
        self.assertEqual(result['per_ip']['10.0.0.50'], 25.0)
        self.assertEqual(result['per_ip']['10.0.0.99'], 5.0)

    def test_aggregate_pivot_noise_unknown_ip_treated_as_zero(self):
        """If an IP in the path has no node, treat its score as 0."""
        from core.scoring import ScoringEngine
        crud = _make_mock_crud()
        crud.select_ip_by_field.return_value = []

        engine = ScoringEngine(crud=crud)
        result = engine.aggregate_pivot_noise(['10.0.0.1'])
        self.assertEqual(result['total_noise'], 0.0)
        self.assertEqual(result['per_ip']['10.0.0.1'], 0.0)

    def test_aggregate_pivot_noise_empty_path(self):
        """Empty path should return 0 total and empty per_ip."""
        from core.scoring import ScoringEngine
        crud = _make_mock_crud()
        engine = ScoringEngine(crud=crud)
        result = engine.aggregate_pivot_noise([])
        self.assertEqual(result['total_noise'], 0.0)
        self.assertEqual(result['per_ip'], {})

    def test_get_opsec_data_includes_aggregate_noise(self):
        """GenericModel.get_opsec_data() should include aggregate_noise from ScoringEngine."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 20.0
        mock_engine.aggregate_pivot_noise.return_value = {
            'total_noise': 35.0,
            'per_ip': {'10.0.0.1': 15.0, '10.0.0.50': 20.0},
        }
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[
                ('10.0.0.1', '', ['ssh'], 0),
                ('10.0.0.50', '10.0.0.1', ['ldap'], 1),
            ]
        )
        result = model.get_opsec_data('10.0.0.50')
        self.assertIn('aggregate_noise', result)
        self.assertEqual(result['aggregate_noise']['total_noise'], 35.0)


# ===========================================================================
# PHASE 3: Risk color mapping
# ===========================================================================

class TestRiskColorMapping(unittest.TestCase):
    """Risk colors (green/yellow/red) based on noise thresholds."""

    def test_risk_color_for_low_score_is_green(self):
        """Score < low threshold → green."""
        from UI.models import risk_color_for_score
        color = risk_color_for_score(5.0)
        self.assertEqual(color, 'green')

    def test_risk_color_for_medium_score_is_yellow(self):
        """Score between low and high threshold → yellow."""
        from UI.models import risk_color_for_score
        color = risk_color_for_score(30.0)
        self.assertEqual(color, 'yellow')

    def test_risk_color_for_high_score_is_red(self):
        """Score >= high threshold → red."""
        from UI.models import risk_color_for_score
        color = risk_color_for_score(70.0)
        self.assertEqual(color, 'red')

    def test_risk_color_for_zero_is_green(self):
        """Zero score → green."""
        from UI.models import risk_color_for_score
        color = risk_color_for_score(0.0)
        self.assertEqual(color, 'green')

    def test_risk_color_custom_thresholds(self):
        """Custom thresholds should override defaults."""
        from UI.models import risk_color_for_score
        # low=10, high=50
        self.assertEqual(risk_color_for_score(5.0, low=10, high=50), 'green')
        self.assertEqual(risk_color_for_score(25.0, low=10, high=50), 'yellow')
        self.assertEqual(risk_color_for_score(55.0, low=10, high=50), 'red')

    def test_risk_color_at_boundary_low(self):
        """Score exactly at low threshold → yellow (not green)."""
        from UI.models import risk_color_for_score
        # default low=20
        color = risk_color_for_score(20.0)
        self.assertEqual(color, 'yellow')

    def test_risk_color_at_boundary_high(self):
        """Score exactly at high threshold → red."""
        from UI.models import risk_color_for_score
        # default high=65
        color = risk_color_for_score(65.0)
        self.assertEqual(color, 'red')


class TestRiskColorInGetOpsecData(unittest.TestCase):
    """get_opsec_data should include risk_color field."""

    def test_get_opsec_data_includes_risk_color(self):
        """get_opsec_data must return a 'risk_color' key."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 50.0
        mock_engine.aggregate_pivot_noise.return_value = {
            'total_noise': 50.0, 'per_ip': {'10.0.0.1': 50.0}
        }
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertIn('risk_color', result)
        self.assertEqual(result['risk_color'], 'yellow')

    def test_get_opsec_data_risk_color_red_for_high_noise(self):
        """High noise score → risk_color='red'."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 80.0
        mock_engine.aggregate_pivot_noise.return_value = {
            'total_noise': 80.0, 'per_ip': {'10.0.0.1': 80.0}
        }
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertEqual(result['risk_color'], 'red')

    def test_get_opsec_data_risk_color_green_without_engine(self):
        """Without scoring engine → noise=0 → risk_color='green'."""
        model = _make_model_with_scoring(
            scoring_engine=None,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertEqual(result['risk_color'], 'green')


# ===========================================================================
# PHASE 4: Tactical suggestions in TreeIPFrame (inline)
# ===========================================================================

class TestTreeIPFrameInlineSuggestions(unittest.TestCase):
    """TreeIPFrame should display inline tactical suggestions."""

    def test_tree_ip_frame_has_suggestions_label(self):
        """TreeIPFrame should have an inline suggestions_label widget."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        self.assertTrue(hasattr(TreeIPFrame, '_update_inline_suggestions'))

    def test_get_opsec_data_includes_suggestions(self):
        """get_opsec_data must include a 'suggestions' list."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 50.0
        mock_engine.aggregate_pivot_noise.return_value = {
            'total_noise': 50.0, 'per_ip': {'10.0.0.1': 50.0}
        }
        model = _make_model_with_scoring(
            scoring_engine=mock_engine,
            cachered_ips=[('10.0.0.1', '', ['ssh'], 0)]
        )
        result = model.get_opsec_data('10.0.0.1')
        self.assertIn('suggestions', result)
        self.assertIsInstance(result['suggestions'], list)

    def test_get_opsec_data_suggestions_from_tactical(self):
        """Suggestions should come from TacticalSuggestions when available."""
        mock_engine = MagicMock()
        mock_engine.get_score.return_value = 50.0
        mock_engine.aggregate_pivot_noise.return_value = {
            'total_noise': 50.0, 'per_ip': {'10.0.0.1': 50.0}
        }

        from UI.models import GenericModel
        repo = MagicMock()
        repo.select_all_ips = MagicMock(return_value=[])
        repo.select_all_ports = MagicMock(return_value=[])

        mock_hooks = MagicMock()
        mock_hooks.on_noise_score_update.return_value = "High noise advisory"
        mock_hooks.on_service_selected.return_value = ["Throttle SSH brute-force"]
        mock_hooks.on_pivot_path_change.return_value = ["Minimal lateral movement"]

        model = GenericModel(
            repository=repo,
            commands=None,
            scoring_engine=mock_engine,
            opsec_hooks=mock_hooks,
        )
        model._cachered = [('10.0.0.1', '', ['ssh'], 0)]

        result = model.get_opsec_data('10.0.0.1')
        # Should have suggestions from noise + service + path advice
        self.assertTrue(len(result['suggestions']) > 0)


class TestTreeIPFrameIsObserver(unittest.TestCase):
    """TreeIPFrame should be an Observer to receive model updates for inline display."""

    def test_tree_ip_frame_has_observer_update(self):
        """TreeIPFrame should implement observer_update for inline suggestions."""
        from UI.frames.tree_ip_frame import TreeIPFrame
        self.assertTrue(hasattr(TreeIPFrame, 'observer_update'))


if __name__ == '__main__':
    unittest.main()
