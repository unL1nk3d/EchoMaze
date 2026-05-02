"""
test_launch.py
TDD tests for the bootstrap layer: build_core_stack() and ScoringEngine wiring.

Validates that:
  1. build_core_stack() creates a real ScoringEngine instance
  2. ScoringEngine is injected into GenericModel
  3. ScoringEngine shares the same CRUD instance as Core
  4. ScoringEngine is attached as observer to GenericModel (bidirectional)
  5. Full bootstrap returns ScoringEngine in its tuple

Run with:
  python -m unittest test_launch -v
"""

import unittest
import sys
from unittest.mock import patch, MagicMock

# -----------------------------------------------------------------------
# Pre-patch: SuggestionsFrame imports pyperclip at module level which may
# not be installed.  We inject a fake pyperclip BEFORE importing launch
# so the transitive import chain  launch → UI.ui → SuggestionsFrame
# doesn't crash.
# -----------------------------------------------------------------------
if 'pyperclip' not in sys.modules:
    sys.modules['pyperclip'] = MagicMock()


class TestBuildCoreStackScoringEngine(unittest.TestCase):
    """build_core_stack() must create and wire a ScoringEngine."""

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_build_core_stack_returns_scoring_engine(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """build_core_stack() must return a ScoringEngine in its return tuple."""
        from launch import build_core_stack
        result = build_core_stack()
        # result should now include scoring_engine somewhere
        # We expect at least 9 items (original 8 + scoring_engine)
        self.assertGreaterEqual(len(result), 9,
            "build_core_stack should return at least 9 items (including scoring_engine)")

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_scoring_engine_is_real_instance(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """The ScoringEngine returned must be a real ScoringEngine instance."""
        from launch import build_core_stack
        from core.scoring import ScoringEngine
        result = build_core_stack()
        # scoring_engine is the last element
        scoring_engine = result[-1]
        self.assertIsInstance(scoring_engine, ScoringEngine)

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_scoring_engine_shares_crud_with_core(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """ScoringEngine must use the SAME crud instance as Core."""
        from launch import build_core_stack
        result = build_core_stack()
        scoring_engine = result[-1]
        crud = result[1]  # crud is the 2nd element returned
        self.assertIs(scoring_engine.crud, crud)

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_generic_model_has_scoring_engine_injected(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """GenericModel inside build_core_stack must receive the ScoringEngine."""
        from launch import build_core_stack
        from core.scoring import ScoringEngine
        result = build_core_stack()
        generic = result[4]  # generic is the 5th element
        scoring_engine = result[-1]
        self.assertIsNotNone(generic.scoring_engine)
        self.assertIs(generic.scoring_engine, scoring_engine)


class TestScoringEngineObserverWiring(unittest.TestCase):
    """ScoringEngine should be wired as observable in the bootstrap."""

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_scoring_engine_is_observable(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """ScoringEngine must be an Observable (has attach/detach/notify)."""
        from launch import build_core_stack
        result = build_core_stack()
        scoring_engine = result[-1]
        self.assertTrue(hasattr(scoring_engine, 'attach'))
        self.assertTrue(hasattr(scoring_engine, 'detach'))
        self.assertTrue(hasattr(scoring_engine, 'notify'))

    @patch('launch.Repository')
    @patch('launch.Configurator')
    @patch('launch.AutoCompleter')
    @patch('launch.DocumentIngestorImp')
    @patch('launch.IngestorUseCase')
    @patch('launch.CRUD_GATHERINGDB')
    @patch('launch.GenericDAO')
    @patch('launch.Core')
    def test_generic_model_attached_to_scoring_engine(
        self, MockCore, MockDAO, MockCRUD, MockIngestorUC,
        MockDocIngestor, MockAuto, MockConfigurator, MockRepo
    ):
        """GenericModel should be attached as observer to ScoringEngine,
        so score_changed events flow to the UI layer."""
        from launch import build_core_stack
        result = build_core_stack()
        generic = result[4]
        scoring_engine = result[-1]
        # GenericModel should be in scoring_engine's observers list
        self.assertIn(generic, scoring_engine._observers)


if __name__ == '__main__':
    unittest.main()
