# --- EDGECASE TESTS: IPNode, scoring, perfiles, pivots (DAO/model) ---
from GATHERINGDB.model import IPNode, PivotHistory
from GATHERINGDB.dao import GenericDAO
from GATHERINGDB.main import CRUD_GATHERINGDB
import unittest
class TestEdgeCasesDAOModel(unittest.TestCase):
    def setUp(self):
        self.dao = CRUD_GATHERINGDB(GenericDAO())  # Assumes test DB or proper context
        # Clean up for isolation
        self.dao.delete_all_ipnodes()
        self.dao.delete_all_pivots()

    def test_ipnode_default_score(self):
        """Crear IPNode sin score explícito (debe ser 0.0 por default)"""
        ip = IPNode(ip="10.1.1.100")
        self.dao.insert_ipnode(ip)
        loaded = self.dao.get_ipnode("10.1.1.100")
        self.assertEqual(loaded.score, 0.0)

    def test_ipnode_score_update(self):
        ip = IPNode(ip="10.1.1.101", score=1.5)
        self.dao.insert_ipnode(ip)
        ip.score = 7.1
        self.dao.update_ipnode(ip)
        loaded = self.dao.get_ipnode("10.1.1.101")
        self.assertEqual(loaded.score, 7.1)

    def test_ipnode_opsec_flag(self):
        ip1 = IPNode(ip="10.1.1.102")
        ip2 = IPNode(ip="10.1.1.103", opsec_flag=2)
        self.dao.insert_ipnode(ip1)
        self.dao.insert_ipnode(ip2)
        self.assertEqual(self.dao.get_ipnode("10.1.1.102").opsec_flag, 0)
        self.assertEqual(self.dao.get_ipnode("10.1.1.103").opsec_flag, 2)

    def test_opsec_flag_update(self):
        ip = IPNode(ip="10.1.1.104", opsec_flag=1)
        self.dao.insert_ipnode(ip)
        ip.opsec_flag = 3
        self.dao.update_ipnode(ip)
        self.assertEqual(self.dao.get_ipnode("10.1.1.104").opsec_flag, 3)

    def test_create_and_get_tunnel(self):
        tun = PivotHistory(src="10.0.0.1", dst="10.0.0.2")
        self.dao.insert_pivot(tun)
        pivots = self.dao.list_pivots()
        self.assertIn(tun, pivots)

    def test_delete_tunnel(self):
        tun = PivotHistory(src="10.0.0.11", dst="10.0.0.12")
        self.dao.insert_pivot(tun)
        self.dao.delete_pivot(tun)
        pivots = self.dao.list_pivots()
        self.assertNotIn(tun, pivots)

    def test_delete_nonexistent_tunnel(self):
        tun = PivotHistory(src="1.2.3.4", dst="5.6.7.8")
        try:
            self.dao.delete_pivot(tun)
            worked = True
        except Exception:
            worked = False
        self.assertTrue(worked)

    def test_ipnode_and_pivot_atomic_create(self):
        ip = IPNode(ip="10.1.1.110")
        tun = PivotHistory(src="10.1.1.110", dst="192.168.5.5")
        self.dao.insert_ipnode(ip)
        self.dao.insert_pivot(tun)
        loaded_ip = self.dao.get_ipnode("10.1.1.110")
        pivots = self.dao.list_pivots()
        self.assertEqual(loaded_ip.ip, tun.src)
        self.assertIn(tun, pivots)

# Fin de los tests de edgecases

