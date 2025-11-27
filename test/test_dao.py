import unittest
from unittest.mock import MagicMock, patch, call
from GATHERINGDB.dao import GenericDAO, Transaction
from GATHERINGDB.model import BaseEntity, IntegrityError

class DummyModel(BaseEntity):
    def __init__(self, id, ip, parent_ip, path):
        self.id = id
        self.ip = ip
        self.parent_ip = parent_ip
        self.path = path

    def exportAsTupple(self):
        return (self.id, self.ip, self.parent_ip, self.path)

    @staticmethod
    def insert():
        return "INSERT INTO ipnode (id, ip, parent_ip, path) VALUES (?, ?, ?, ?)"

    @staticmethod
    def update():
        return "UPDATE ipnode SET id=?, ip=?, parent_ip=?, path=? WHERE id=?"

    @staticmethod
    def delete():
        return "DELETE FROM ipnode WHERE id=?"

    @staticmethod
    def select():
        return "SELECT id, ip, parent_ip, path FROM ipnode"

    @staticmethod
    def selectById():
        return "SELECT id, ip, parent_ip, path FROM ipnode WHERE id=?"

    @staticmethod
    def selectCoincidence(field):
        return f"SELECT id, ip, parent_ip, path FROM ipnode WHERE {field}=?"

class TestGenericDAO(unittest.TestCase):
    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.patcher = patch('GATHERINGDB.dao.SQLiteConnectionPool', return_value=self.mock_conn)
        self.patcher.start()
        GenericDAO.conn = MagicMock(return_value=self.mock_conn)

    def tearDown(self):
        self.patcher.stop()

    def test_insertar_success(self):
        model = DummyModel(1, '192.168.1.1', '', '/')
        self.mock_cursor.rowcount = 1
        result = GenericDAO.insertar(model)
        self.mock_cursor.execute.assert_called_once_with(model.insert(), model.exportAsTupple())
        self.assertEqual(result, 1)

    def test_insertar_integrity_error(self):
        model = DummyModel(1, '192.168.1.1', '', '/')
        self.mock_cursor.execute.side_effect = sqlite3.IntegrityError("duplicate")
        with self.assertRaises(IntegrityError):
            GenericDAO.insertar(model)

    def test_actualizar_success(self):
        model = DummyModel(1, '192.168.1.1', '', '/')
        self.mock_cursor.rowcount = 1
        result = GenericDAO.actualizar(model, 1)
        expected_values = list(model.exportAsTupple()) + [1]
        self.mock_cursor.execute.assert_called_once_with(model.update(), expected_values)
        self.assertEqual(result, 1)

    def test_eliminar_success(self):
        model = DummyModel(1, '192.168.1.1', '', '/')
        self.mock_cursor.rowcount = 1
        result = GenericDAO.eliminar(model, 1)
        self.mock_cursor.execute.assert_called_once_with(model.delete(), (1,))
        self.assertEqual(result, 1)

    def test_seleccionarPorId_found(self):
        self.mock_cursor.fetchone.return_value = (1, '192.168.1.1', '', '/')
        result = GenericDAO.seleccionarPorId(DummyModel, 1)
        self.mock_cursor.execute.assert_called_once()
        self.assertIsInstance(result, DummyModel)
        self.assertEqual(result.ip, '192.168.1.1')

    def test_seleccionarPorId_not_found(self):
        self.mock_cursor.fetchone.return_value = None
        result = GenericDAO.seleccionarPorId(DummyModel, 99)
        self.assertIsNone(result)

    def test_seleccionarCoincidencia(self):
        self.mock_cursor.fetchall.return_value = [
            (1, '192.168.1.1', '', '/'),
            (2, '192.168.1.2', '', '/')
        ]
        result = GenericDAO.seleccionarCoincidencia(DummyModel, 'ip', '192.168.1.1')
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], DummyModel)

    def test_seleccionar_top_results(self):
        self.mock_cursor.fetchmany.return_value = [
            (1, '192.168.1.1', '', '/'),
            (2, '192.168.1.2', '', '/')
        ]
        result = GenericDAO.seleccionar(DummyModel, top_results=2)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[1], DummyModel)

class TestTransaction(unittest.TestCase):
    def test_transaction_commit(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        pool = MagicMock(return_value=MagicMock(get_connection=MagicMock(return_value=conn)))

        with Transaction(conn, pool) as cur:
            cur.execute("SELECT 1")

        conn.commit.assert_called_once()
        cursor.close.assert_called_once()

    def test_transaction_rollback_on_exception(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        pool = MagicMock(return_value=MagicMock(get_connection=MagicMock(return_value=conn)))

        try:
            with Transaction(conn, pool) as cur:
                raise ValueError("Simulated error")
        except ValueError:
            pass

        conn.rollback.assert_called_once()
        cursor.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
