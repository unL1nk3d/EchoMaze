import unittest
from unittest.mock import MagicMock, patch
from GATHERINGDB.crud_mitre import CRUD_ACTIONS
from GATHERINGDB.model import Actions, IPNode
from GATHERINGDB.log import log


class TestCRUDActions(unittest.TestCase):
    def setUp(self):
        self.mock_dao = MagicMock()
        self.crud_actions = CRUD_ACTIONS()

    def test_insert_action_success(self):
        """Test inserción exitosa de una acción"""
        # Mock del nodo IPNode existente
        mock_node = MagicMock(spec=IPNode)
        mock_node.id = 1
        self.mock_dao.seleccionarPorId.return_value = mock_node

        result = self.crud_actions.insert_action(
            node_id=1,
            action_type="nmap_scan",
            command_template="nmap -sV {target}",
            parameters='{"target": "192.168.1.100"}',
            mitre_ttp_id="T1046",
            operator="analyst1",
            noise_score=0.3,
            dao=self.mock_dao
        )

        # Verificar que se insertó
        self.mock_dao.insertar.assert_called_once()
        inserted_action = self.mock_dao.insertar.call_args[0][0]
        self.assertIsInstance(inserted_action, Actions)
        self.assertEqual(inserted_action.action_type, "nmap_scan")
        self.assertEqual(inserted_action.node_id, 1)
        self.assertEqual(inserted_action.noise_score, 0.3)

    def test_insert_action_node_not_found(self):
        """Test inserción de acción cuando el nodo no existe"""
        self.mock_dao.seleccionarPorId.return_value = None

        with self.assertRaises(ValueError) as context:
            self.crud_actions.insert_action(
                node_id=999,
                action_type="nmap_scan",
                command_template="nmap -sV {target}",
                parameters='{"target": "192.168.1.100"}',
                mitre_ttp_id="T1046",
                operator="analyst1",
                dao=self.mock_dao
            )
        self.assertIn("No IPNode found", str(context.exception))

    def test_insert_action_db_error(self):
        """Test inserción de acción con error de BD"""
        mock_node = MagicMock(spec=IPNode)
        self.mock_dao.seleccionarPorId.return_value = mock_node
        self.mock_dao.insertar.side_effect = Exception("DB connection error")

        with self.assertRaises(Exception):
            self.crud_actions.insert_action(
                node_id=1,
                action_type="nmap_scan",
                command_template="nmap -sV {target}",
                parameters='{"target": "192.168.1.100"}',
                mitre_ttp_id="T1046",
                operator="analyst1",
                dao=self.mock_dao
            )

    def test_select_all_actions_success(self):
        """Test obtener todas las acciones"""
        mock_actions = [
            MagicMock(spec=Actions, id=1, action_type="nmap_scan", node_id=1),
            MagicMock(spec=Actions, id=2, action_type="web_scan", node_id=2),
        ]
        self.mock_dao.seleccionar.return_value = mock_actions

        result = self.crud_actions.select_all_actions(dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].action_type, "nmap_scan")
        self.assertEqual(result[1].action_type, "web_scan")
        self.mock_dao.seleccionar.assert_called_once_with(Actions)

    def test_select_all_actions_empty(self):
        """Test obtener acciones cuando no hay"""
        self.mock_dao.seleccionar.return_value = []

        result = self.crud_actions.select_all_actions(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_all_actions_db_error(self):
        """Test obtener acciones con error de BD"""
        self.mock_dao.seleccionar.side_effect = Exception("DB error")

        result = self.crud_actions.select_all_actions(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_actions_by_node_success(self):
        """Test obtener acciones de un nodo específico"""
        mock_actions = [
            MagicMock(spec=Actions, id=1, action_type="nmap_scan", node_id=1),
            MagicMock(spec=Actions, id=2, action_type="web_scan", node_id=2),
            MagicMock(spec=Actions, id=3, action_type="ssh_enum", node_id=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_actions

        result = self.crud_actions.select_actions_by_node(node_id=1, dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(a.node_id == 1 for a in result))

    def test_select_actions_by_node_not_found(self):
        """Test obtener acciones de un nodo que no tiene acciones"""
        mock_actions = [
            MagicMock(spec=Actions, id=1, action_type="nmap_scan", node_id=2),
        ]
        self.mock_dao.seleccionar.return_value = mock_actions

        result = self.crud_actions.select_actions_by_node(node_id=999, dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_actions_by_mitre_ttp_success(self):
        """Test obtener acciones por MITRE TTP"""
        mock_actions = [
            MagicMock(spec=Actions, id=1, action_type="nmap_scan", mitre_ttp_id="T1046"),
            MagicMock(spec=Actions, id=2, action_type="web_scan", mitre_ttp_id="T1589"),
            MagicMock(spec=Actions, id=3, action_type="port_scan", mitre_ttp_id="T1046"),
        ]
        self.mock_dao.seleccionar.return_value = mock_actions

        result = self.crud_actions.select_actions_by_mitre_ttp(mitre_ttp_id="T1046", dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(a.mitre_ttp_id == "T1046" for a in result))

    def test_select_actions_by_mitre_ttp_not_found(self):
        """Test obtener acciones por MITRE TTP inexistente"""
        mock_actions = [
            MagicMock(spec=Actions, id=1, action_type="nmap_scan", mitre_ttp_id="T1046"),
        ]
        self.mock_dao.seleccionar.return_value = mock_actions

        result = self.crud_actions.select_actions_by_mitre_ttp(mitre_ttp_id="T9999", dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_update_action_success(self):
        """Test actualización exitosa de una acción"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        mock_action.action_type = "nmap_scan"
        mock_action.command_template = "nmap -sV {target}"
        mock_action.noise_score = 0.3

        self.mock_dao.seleccionar.return_value = [mock_action]

        self.crud_actions.update_action(
            action_id=1,
            action_type="nmap_aggressive",
            noise_score=0.7,
            dao=self.mock_dao
        )

        self.assertEqual(mock_action.action_type, "nmap_aggressive")
        self.assertEqual(mock_action.noise_score, 0.7)
        self.mock_dao.actualizar.assert_called_once_with(mock_action, 1)

    def test_update_action_not_found(self):
        """Test actualización de acción inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_actions.update_action(
                action_id=999,
                action_type="new_type",
                dao=self.mock_dao
            )
        self.assertIn("No Action found", str(context.exception))

    def test_update_action_partial_fields(self):
        """Test actualización parcial de campos"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        mock_action.action_type = "nmap_scan"
        mock_action.command_template = "nmap -sV {target}"
        mock_action.parameters = '{"target": "192.168.1.100"}'
        mock_action.noise_score = 0.3

        self.mock_dao.seleccionar.return_value = [mock_action]

        self.crud_actions.update_action(
            action_id=1,
            noise_score=0.9,
            dao=self.mock_dao
        )

        # Solo noise_score debe cambiar
        self.assertEqual(mock_action.action_type, "nmap_scan")  # sin cambios
        self.assertEqual(mock_action.noise_score, 0.9)  # actualizado

    def test_delete_action_success(self):
        """Test eliminación exitosa de una acción"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        self.mock_dao.seleccionar.return_value = [mock_action]

        self.crud_actions.delete_action(action_id=1, dao=self.mock_dao)

        self.mock_dao.eliminar.assert_called_once_with(mock_action, 1)

    def test_delete_action_not_found(self):
        """Test eliminación de acción inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_actions.delete_action(action_id=999, dao=self.mock_dao)
        self.assertIn("No Action found", str(context.exception))

    def test_delete_action_db_error(self):
        """Test eliminación con error de BD"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        self.mock_dao.seleccionar.return_value = [mock_action]
        self.mock_dao.eliminar.side_effect = Exception("DB error")

        with self.assertRaises(Exception):
            self.crud_actions.delete_action(action_id=1, dao=self.mock_dao)


if __name__ == '__main__':
    unittest.main()