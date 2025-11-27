import os
import tempfile
import pathlib
import shutil
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from core import Core

class FakeCRUDBasic:
    def __init__(self):
        self.dao = None
        self.inserted_ips = []
        self.inserted_ports = []
        self.ip_records = {}
        self.port_records = {}

    def select_ip_by_field(self, field, value, dao=None):
        # return list-like of ip entities if exists
        return self.ip_records.get(value, [])

    def select_port_by_field(self, field, value, dao=None):
        # value is ip string here (method in Core passes ip_entity.ip)
        return self.port_records.get(value, [])

    def insert_ip(self, ip, path, parent, child_level=0, dao=None):
        self.inserted_ips.append((ip, path, parent, child_level))
        # also register so subsequent select_ip_by_field returns something
        entity = SimpleNamespace(id=len(self.inserted_ips), ip=ip, path=path, parent_ip=parent)
        self.ip_records[ip] = [entity]
        return entity

    def insert_port_node(self, ip_id, port, service_name=None, dao=None):
        self.inserted_ports.append((ip_id, port, service_name))
        return True

class TestCoreIPDirSubsystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_detect_ip_directories(self):
        base = self.tmpdir / "scan_results"
        (base / "192.168.1.1").mkdir(parents=True)
        (base / "not_an_ip").mkdir()
        (base / "10.0.0.5").mkdir()
        core = Core()
        res = core.detect_ip_directories(base_dir=str(base))
        # must return only directories with valid IPv4 names
        names = [name for (_path, name) in res]
        self.assertIn("192.168.1.1", names)
        self.assertIn("10.0.0.5", names)
        self.assertNotIn("not_an_ip", names)

    def test_insert_ip_from_directory_recursive_inserts(self):
        # build nested structure:
        # base / host-192.168.1.1 / child-192.168.1.2
        base = self.tmpdir / "scan_results"
        nested = base / "host-192.168.1.1" / "child-192.168.1.2"
        nested.mkdir(parents=True)
        # stub Core to avoid real service insertion
        fake = FakeCRUDBasic()
        core = Core(crud=fake)
        # patch insert_services_from_directory so test only verifies IP insertion recursion
        core.insert_services_from_directory = MagicMock()
        core.insert_ip_from_directory(str(base))
        # expect both IPs inserted
        inserted_ips = [t[0] for t in fake.inserted_ips]
        self.assertTrue(any("192.168.1.1" in name for name in inserted_ips))
        self.assertTrue(any("192.168.1.2" in name for name in inserted_ips))

    def test_resolve_service_name_named_numeric_and_ip(self):
        mapping = {80: "http", 8080: "http-alt"}
        core = Core(PORT_SERVICE_MAP=mapping)
        core.port_service_map = mapping
        # named service
        self.assertEqual(core.resolve_service_name("http"), 80)
        # numeric string
        self.assertEqual(core.resolve_service_name("8080"), 8080)
        # ip-looking string should return None (function treats dotted names as IPs)
        self.assertIsNone(core.resolve_service_name("1.2.3.4"))

    def test_insert_services_from_directory_inserts_ports(self):
        base = self.tmpdir / "1.2.3.4"
        base.mkdir(parents=True)
        # create service dirs: 'http' and '8080'
        (base / "http").mkdir()
        (base / "8080").mkdir()
        fake = FakeCRUDBasic()
        # pre-register IP entity returned by select_ip_by_field
        fake.ip_records["1.2.3.4"] = [SimpleNamespace(id=7, ip="1.2.3.4", path=str(base), parent_ip="")]
        # ensure no ports pre-existing
        fake.port_records["1.2.3.4"] = []
        core = Core(crud=fake, PORT_SERVICE_MAP={80: "http", 8080: "8080"})
        core.port_service_map = {80: "http", 8080: "8080"}
        core.insert_services_from_directory(str(base), "1.2.3.4")
        # should insert both http->80 and numeric 8080
        inserted = {(t[1], t[2]) for t in fake.inserted_ports}
        self.assertIn((80, "http"), inserted)
        self.assertIn((8080, '8080'), inserted)  # numeric service stored as port name fallback

    def test_check_already_inserted_ip_and_port(self):
        fake = FakeCRUDBasic()
        # register IP entity
        fake.ip_records["2.2.2.2"] = [SimpleNamespace(id=3, ip="2.2.2.2", path="", parent_ip="")]
        # no ports -> should be False
        fake.port_records["2.2.2.2"] = []
        core = Core(crud=fake, PORT_SERVICE_MAP={})
        self.assertTrue(core.check_already_inserted_ip("2.2.2.2"))
        self.assertFalse(core.check_already_inserted_port("2.2.2.2", 22))
        # add a port record
        fake.port_records["2.2.2.2"] = [SimpleNamespace(port=22)]
        self.assertTrue(core.check_already_inserted_port("2.2.2.2", 22))

if __name__ == "__main__":
    unittest.main()