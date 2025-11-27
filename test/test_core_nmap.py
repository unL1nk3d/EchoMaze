import os
import tempfile
import unittest
from types import SimpleNamespace

from core import Core


class TestCore(unittest.TestCase):
	def test_parse_greppable_nmap(self):
		import pathlib
		tmpdir = pathlib.Path(tempfile.mkdtemp())
		content = (
			"Host: 192.168.1.1 ()\tPorts: 22/open/tcp//ssh///,80/open/tcp//http///\n"
			"Host: 10.0.0.5 ()\tPorts: 21/open/tcp//ftp///,25/open/tcp//smtp///\n"
		)
		file = tmpdir / "scan.gnmap"
		file.write_text(content)

		core = Core()
		result = core.parse_greppable_nmap(str(file))

		self.assertIsInstance(result, dict)
		self.assertIn("192.168.1.1", result)
		self.assertIn(22, result["192.168.1.1"])
		self.assertIn(80, result["192.168.1.1"])
		self.assertIn("10.0.0.5", result)
		self.assertIn(21, result["10.0.0.5"])

	def test_create_ip_directories(self):
		import pathlib
		tmpdir = pathlib.Path(tempfile.mkdtemp())
		core = Core(PORT_SERVICE_MAP={80: 'http', 22: 'ssh'})
		ip_ports = {'192.168.1.1': [80, 22]}
		base = tmpdir / "scan_results"
		core.create_ip_directories(ip_ports, base_dir=str(base))

		self.assertTrue((base / '192.168.1.1').is_dir())
		self.assertTrue((base / '192.168.1.1' / 'http').is_dir())
		self.assertTrue((base / '192.168.1.1' / 'ssh').is_dir())

	def test_insert_ip_from_nmap_calls_crud_methods(self):
		calls = {'select_ip_by_field': [], 'insert_ip': [], 'insert_port_node': []}

		class FakeCRUD:
			def __init__(self):
				self.dao = None
				self.calls = {'select_ip_by_field': [], 'insert_ip': [], 'insert_port_node': []}
			def select_ip_by_field(self, field, value, dao=None):
				self.calls['select_ip_by_field'].append((field, value))
				return []

			def insert_ip(self, ip, path, parent, dao=None):
				self.calls['insert_ip'].append((ip, path, parent))

			def insert_port_node(self, ip_id, port, dao=None):
				self.calls['insert_port_node'].append((ip_id, port))

		fake = FakeCRUD()
		core = Core(crud=fake, PORT_SERVICE_MAP={80: 'http'})
		ip_ports = {'1.2.3.4': [80]}
		core.insert_ip_from_nmap(ip_ports)
		self.assertEqual(len(fake.calls['select_ip_by_field']), 2)
 		# se invoca 3 veces por self.Insert ports from nmap
		self.assertEqual(len(fake.calls['insert_ip']), 1)

	def test_insert_ports_from_nmap_uses_crud(self):
		calls = {'select_ip_by_field': [], 'insert_port_node': []}
  
		class ModelPtMock:
			def __init__(self, id, ip, path, parent_ip):      
				self.id:int = id 
				self.ip:str = ip
				self.path:str = path
				self.parent_ip:str = parent_ip
		class FakeCRUD:
			def __init__(self):
				self.dao = None
				self.calls = {'select_ip_by_field': [], 'insert_port_node': []}
    
			def select_ip_by_field(self, field, value, dao=None):
				self.calls['select_ip_by_field'].append((field, value))
				return [ModelPtMock(42,'1.1.1.1','','')]

			def insert_port_node(self, ip_id, port, dao=None):
				self.calls['insert_port_node'].append((ip_id, port))

		fake = FakeCRUD()
		core = Core(crud=fake)
		core.insert_ports_from_nmap('1.2.3.4', [22, 80])

		self.assertGreaterEqual(len(fake.calls['select_ip_by_field']), 1)
		self.assertIn((42, 22), fake.calls['insert_port_node'])
		self.assertIn((42, 80), fake.calls['insert_port_node'])

if __name__ == '__main__':
	unittest.main()
