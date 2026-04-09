import unittest
from unittest.mock import MagicMock, patch
from core.scoring import ScoringEngine

class TestScoringEngine(unittest.TestCase):
    def setUp(self):
        # Mocks para CRUD_GATHERINGDB y su DAO
        self.mock_crud = MagicMock()
        self.mock_crud.dao = MagicMock()  # necesario para pasar como argumento
        self.ip_node = MagicMock()
        self.ip_node.id = 5
        self.ip_node.ip = '1.2.3.4'
        self.ip_node.score = 0.0
        self.ip_node.opsec_flag = 1
        # Por defecto, retorna un IPNode para select
        self.mock_crud.select_ip_by_field.side_effect = lambda field, value, dao=None: [self.ip_node] if value == self.ip_node.ip else []
        self.mock_crud.insert_ip = MagicMock()
        self.mock_crud.update_ip = MagicMock()

    def test_register_action_ip_exists(self):
        engine = ScoringEngine(crud=self.mock_crud)
        self.ip_node.score = 3.0
        score = engine.register_action('1.2.3.4', 'scan')
        self.assertAlmostEqual(score, 3.0 + 5*1.3)
        self.mock_crud.update_ip.assert_called_with(self.ip_node.id, self.ip_node, dao=self.mock_crud.dao)

    def test_register_action_ip_not_exists(self):
        engine = ScoringEngine(crud=self.mock_crud)
        # Simula: primero no existe (None), después sí existe
        with patch.object(engine, '_find_ipnode', side_effect=[None, self.ip_node]):
            engine.register_action('8.8.8.8', 'enum')
            self.mock_crud.insert_ip.assert_called()
            self.mock_crud.update_ip.assert_called()

    def test_get_score(self):
        engine = ScoringEngine(crud=self.mock_crud)
        self.ip_node.score = 25.0
        score = engine.get_score('1.2.3.4')
        self.assertEqual(score, 25.0)
        # Sin node
        score_none = engine.get_score('9.9.9.9')
        self.assertEqual(score_none, 0.0)

    def test_set_profile(self):
        engine = ScoringEngine(crud=self.mock_crud)
        engine.set_profile('1.2.3.4', 2)
        self.assertEqual(self.ip_node.opsec_flag, 2)
        self.mock_crud.update_ip.assert_called()

    def test_set_profile_node_not_exists(self):
        engine = ScoringEngine(crud=self.mock_crud)
        with patch.object(engine, '_find_ipnode', side_effect=[None, self.ip_node]):
            engine.set_profile('8.8.4.4', 0)
            self.mock_crud.insert_ip.assert_called()
            self.mock_crud.update_ip.assert_called()

    def test_reset_score(self):
        engine = ScoringEngine(crud=self.mock_crud)
        self.ip_node.score = 120.2
        engine.reset_score('1.2.3.4')
        self.assertEqual(self.ip_node.score, 0.0)
        self.mock_crud.update_ip.assert_called()
    
    def test_reset_score_no_node(self):
        engine = ScoringEngine(crud=self.mock_crud)
        with patch.object(engine, '_find_ipnode', return_value=None):
            engine.reset_score('7.7.7.7')  # No debe romper ni llamar update
            self.mock_crud.update_ip.assert_not_called()

    def test_score_threshold(self):
        engine = ScoringEngine(crud=self.mock_crud)
        self.ip_node.opsec_flag = 0
        self.assertEqual(engine.score_threshold('1.2.3.4'), 20)
        self.ip_node.opsec_flag = 2
        self.assertEqual(engine.score_threshold('1.2.3.4'), 65)
        self.ip_node.opsec_flag = 7
        self.assertEqual(engine.score_threshold('1.2.3.4'), 40)

    def test_profile_mod_default_and_override(self):
        engine = ScoringEngine(crud=self.mock_crud)
        self.ip_node.opsec_flag = 2
        self.assertAlmostEqual(engine._get_profile_mod(self.ip_node), 1.7)
        self.assertAlmostEqual(engine._get_profile_mod(self.ip_node, override_profile=0), 1.0)
        self.assertAlmostEqual(engine._get_profile_mod(self.ip_node, override_profile=8), 1.3)

    def test_inject_custom_config_dicts(self):
        custom_scores = {'special': 99}
        custom_mod = {10: 4.5}
        custom_thr = {10: 256}
        engine = ScoringEngine(
            crud=self.mock_crud, action_scores=custom_scores, profile_modifiers=custom_mod, thresholds=custom_thr
        )
        self.ip_node.opsec_flag = 10
        score = engine.register_action('1.2.3.4', 'special')
        self.assertAlmostEqual(score, 99*4.5)
        self.assertEqual(engine.score_threshold('1.2.3.4'), 256)
        self.assertAlmostEqual(engine._get_profile_mod(self.ip_node), 4.5)

if __name__ == '__main__':
    unittest.main()
