import unittest
import sqlite3
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.model import WorkflowScoreConfig, PivotHistory, IPNode

class TestWorkflowScoreConfigDAO(unittest.TestCase):
    def setUp(self):
        GenericDAO.createTable(WorkflowScoreConfig)
        # Clean up after each test (delete all)
        self._cleanup()

    def _cleanup(self):
        with GenericDAO.conn() as connection:
            connection.execute("DELETE FROM workflow_score_config")
            connection.commit()

    def test_crud_cycle(self):
        cfg = WorkflowScoreConfig(id=None, name="stealth", value=1.0, description="Stealth test")
        # Insert
        inserted = GenericDAO.insertar(cfg)
        self.assertEqual(inserted, 1)
        # Read
        results = GenericDAO.seleccionar(WorkflowScoreConfig)
        self.assertEqual(len(results), 1)
        obj = results[0]
        self.assertEqual(obj.name, "stealth")
        # Update
        obj.name = "stealth2"
        obj.value = 2.5
        updated = GenericDAO.actualizar(obj, obj.id)
        self.assertGreaterEqual(updated, 1)
        updated_obj = GenericDAO.seleccionarPorId(WorkflowScoreConfig, obj.id)
        self.assertEqual(updated_obj.name, "stealth2")
        # Delete
        deleted = GenericDAO.eliminar(obj, obj.id)
        self.assertGreaterEqual(deleted, 1)
        results = GenericDAO.seleccionar(WorkflowScoreConfig)
        self.assertEqual(len(results), 0)

    def tearDown(self):
        self._cleanup()

class TestPivotHistoryDAO(unittest.TestCase):
    def setUp(self):
        GenericDAO.createTable(PivotHistory)
        self._cleanup()

    def _cleanup(self):
        with GenericDAO.conn() as connection:
            connection.execute("DELETE FROM pivot_history")
            connection.commit()

    def test_crud_cycle(self):
        record = PivotHistory(id=None, source_ip="1.1.1.1", dest_ip="2.2.2.2", operator="tester", timestamp="2023-01-01T11:00:00", details="first test")
        result = GenericDAO.insertar(record)
        self.assertEqual(result, 1)
        objs = GenericDAO.seleccionar(PivotHistory)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj.operator, "tester")
        # Update
        obj.details = "modified"
        changed = GenericDAO.actualizar(obj, obj.id)
        self.assertGreaterEqual(changed, 1)
        after = GenericDAO.seleccionarPorId(PivotHistory, obj.id)
        self.assertEqual(after.details, "modified")
        # Delete
        deleted = GenericDAO.eliminar(obj, obj.id)
        self.assertGreaterEqual(deleted, 1)
        self.assertEqual(len(GenericDAO.seleccionar(PivotHistory)), 0)

    def tearDown(self):
        self._cleanup()

class TestIPNodeExtraFields(unittest.TestCase):
    def setUp(self):
        GenericDAO.createTable(IPNode)
        self._cleanup()

    def _cleanup(self):
        with GenericDAO.conn() as connection:
            connection.execute("DELETE FROM ip_node")
            connection.commit()

    def test_score_and_opsec_flag(self):
        node = IPNode(id=None, ip="10.0.0.10", path="/", parent_ip=None, child_level=1, score=7.5, opsec_flag=1)
        result = GenericDAO.insertar(node)
        self.assertEqual(result, 1)
        objs = GenericDAO.seleccionar(IPNode)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj.score, 7.5)
        self.assertEqual(obj.opsec_flag, 1)
        # Update
        obj.score = 8.25
        obj.opsec_flag = 0
        updated = GenericDAO.actualizar(obj, obj.id)
        self.assertGreaterEqual(updated, 1)
        after = GenericDAO.seleccionarPorId(IPNode, obj.id)
        self.assertEqual(after.score, 8.25)
        self.assertEqual(after.opsec_flag, 0)

    def tearDown(self):
        self._cleanup()

if __name__ == "__main__":
    unittest.main()
