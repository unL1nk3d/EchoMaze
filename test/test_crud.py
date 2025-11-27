import unittest
from unittest.mock import MagicMock
from GATHERINGDB.model import IPNode, Ports
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB  

class TestCRUD_GATHERINGDB(unittest.TestCase):
    def setUp(self):
        self.mock_dao = MagicMock(spec=GenericDAO)
        self.crud = CRUD_GATHERINGDB(dao=self.mock_dao)

    def test_select_ip_by_field_success(self):
        self.mock_dao.seleccionarCoincidencia.return_value = [IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')]
        result = self.crud.select_ip_by_field('ip', '192.168.1.1', dao=self.mock_dao)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ip, '192.168.1.1')

    def test_select_ip_by_field_failure(self):
        self.mock_dao.seleccionarCoincidencia.side_effect = Exception("DB error")
        result = self.crud.select_ip_by_field('ip', '192.168.1.1', dao=self.mock_dao)
        self.assertEqual(result, [])

    def test_insert_port_node_success(self):
        ipnode = IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')
        self.mock_dao.seleccionarPorId.return_value = ipnode
        self.crud.insert_port_node(1, 8080, dao=self.mock_dao)
        self.mock_dao.insertar.assert_called_once()
        args = self.mock_dao.insertar.call_args[0][0]
        self.assertIsInstance(args, Ports)
        self.assertEqual(args.port, 8080)

    def test_insert_port_node_invalid_ip(self):
        self.mock_dao.seleccionarPorId.return_value = None
        #with self.assertLogs('GATHERINGDB.log', level='ERROR'):
        self.crud.insert_port_node(99, 8080, dao=self.mock_dao)

    def test_insert_ip(self):
        self.crud.insert_ip('192.168.1.2', '/path', '192.168.1.1', dao=self.mock_dao)
        self.mock_dao.insertar.assert_called_once()
        ipnode = self.mock_dao.insertar.call_args[0][0]
        self.assertEqual(ipnode.ip, '192.168.1.2')

    def test_show_all_data(self):
        self.mock_dao.seleccionar.return_value = [IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')]
        count = self.crud.show_all_data(IPNode, dao=self.mock_dao)
        self.assertEqual(count, 1)

    def test_select(self):
        self.mock_dao.seleccionar.return_value = [IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')]
        result = self.crud.select(IPNode, dao=self.mock_dao)
        self.assertEqual(len(result), 1)

    def test_delete_ip_success(self):
        ipnode = IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')
        self.mock_dao.seleccionarPorId.return_value = ipnode
        self.crud.delete_ip(1, dao=self.mock_dao)
        self.mock_dao.eliminar.assert_called_once_with(ipnode, 1)

    def test_delete_ip_not_found(self):
        self.mock_dao.seleccionarPorId.return_value = None
        #with self.assertLogs('GATHERINGDB.log', level='ERROR'):
        self.crud.delete_ip(99, dao=self.mock_dao)

    def test_update_ip_success(self):
        ipnode = IPNode(id=1, ip='192.168.1.1', parent_ip='', path='/')
        self.mock_dao.seleccionarPorId.return_value = ipnode
        self.crud.update_ip(1, ipnode, dao=self.mock_dao)
        self.mock_dao.actualizar.assert_called_once_with(ipnode, 1)

    def test_update_ip_not_found(self):
        self.mock_dao.seleccionarPorId.return_value = None
        #with self.assertLogs('GATHERINGDB.log', level='ERROR'):
        self.crud.update_ip(99, IPNode(id=99, ip='192.168.1.99', parent_ip='', path='/'), dao=self.mock_dao)
    def test_select_depth_ips_returns_nodes(self):
        # Simula la respuesta para child_level
        def seleccionarCoincidencia(data, field, value):
            if field == 'child_level':
                return [IPNode(id=1, ip=f'192.168.0.{value}', parent_ip='', child_level=value, path='/')]
            return []
        self.mock_dao.seleccionarCoincidencia.side_effect = seleccionarCoincidencia

        res = self.crud.select_depth_ips(3, dao=self.mock_dao)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].child_level, 3)
        self.mock_dao.seleccionarCoincidencia.assert_called_with(IPNode, 'child_level', 3)

    def test_select_ip_parents_yields_levels_and_caps(self):
        # max_child_level_by_parent indica max_level = 1 => cap a 1 aunque pidamos depth=5
        def seleccionarCoincidencia(data, field, value):
            if field == 'max_child_level_by_parent':
                return [MagicMock(max_level=1)]
            if field == 'child_level':
                return [IPNode(id=1, ip=f'10.0.0.{value}', parent_ip='', child_level=value, path='/')]
            return []
        self.mock_dao.seleccionarCoincidencia.side_effect = seleccionarCoincidencia

        gen = self.crud.select_ip_parents('192.168.0.1', 5, dao=self.mock_dao)
        levels = list(gen)
        # Debe producir resultados para level 0 y 1 (cap)
        self.assertEqual(len(levels), 2)
        self.assertEqual(levels[0][0].child_level, 0)
        self.assertEqual(levels[1][0].child_level, 1)
        self.mock_dao.seleccionarCoincidencia.assert_any_call(IPNode, 'max_child_level_by_parent', '192.168.0.1')
        self.mock_dao.seleccionarCoincidencia.assert_any_call(IPNode, 'child_level', 0)
        self.mock_dao.seleccionarCoincidencia.assert_any_call(IPNode, 'child_level', 1)

    def test_select_ip_parents_parent_not_found_returns_empty(self):
        # Si no hay registro de max_level debe retornar lista vacía
        self.mock_dao.seleccionarCoincidencia.return_value = []
        res = list(self.crud.select_ip_parents('no-existe', 2, dao=self.mock_dao))
        self.assertEqual(res, [])

if __name__ == '__main__':
    unittest.main()
