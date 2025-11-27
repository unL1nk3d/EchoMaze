import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import commands

class TestLaunchCommands(unittest.TestCase):

    @patch('commands.DatabaseInitializer')
    def test_check_db_created_calls_initializer(self, mock_dbinit):
        fake_core = SimpleNamespace(crud=SimpleNamespace(dao='TEST_DAO'))
        cmd = commands.Commands(core=fake_core)

        cmd.check_db_created()

        mock_dbinit.check_db_created.assert_called_once_with(fake_core, fake_core.crud.dao)

    def test_import_from_nmap_scan_invokes_core_methods(self):
        fake_core = SimpleNamespace()
        fake_core.parse_greppable_nmap = Mock(return_value={'1.2.3.4': [80]})
        fake_core.create_ip_directories = Mock()
        fake_core.insert_ip_from_nmap = Mock()

        cmd = commands.Commands(core=fake_core)
        cmd.import_from_nmap_scan()

        fake_core.parse_greppable_nmap.assert_called_once_with('nmap_scan.gnmap')
        fake_core.create_ip_directories.assert_called_once_with({'1.2.3.4': [80]}, base_dir=os.getcwd())
        fake_core.insert_ip_from_nmap.assert_called_once_with(ip_ports={'1.2.3.4': [80]})

    def test_reload_from_directory_calls_insert_ip_from_directory(self):
        fake_core = SimpleNamespace(insert_ip_from_directory=Mock())
        cmd = commands.Commands(core=fake_core)

        cmd.reload_from_directory()

        fake_core.insert_ip_from_directory.assert_called_once_with(os.getcwd())


if __name__ == '__main__':
    unittest.main()
