"""
Tests para el módulo LogImporter
=================================

Tests unitarios e integración para:
- Parsers de diferentes formatos
- LogImportManager
- Integración con GATHERINGDB
"""

import unittest
import json
import tempfile
import os
from pathlib import Path

from logimporter.importer import (
    LogImporter,
    PlainTextParser,
    JSONParser,
    CSVParser,
    BashHistoryParser,
    ZshHistoryParser,
    CommandEvent,
    ImportReport,
    LogFormatDetector
)
from logimporter.manager import LogImportManager, LogImportValidator


class TestCommandEvent(unittest.TestCase):
    """Tests para CommandEvent."""
    
    def test_create_valid_event(self):
        """Crear un evento válido."""
        event = CommandEvent(command="whoami")
        self.assertEqual(event.command, "whoami")
        self.assertIsNotNone(event.import_time)
    
    def test_event_requires_command(self):
        """Un evento sin comando debe fallar."""
        with self.assertRaises(ValueError):
            CommandEvent(command="")
    
    def test_event_strips_whitespace(self):
        """Los espacios en blanco se deben eliminar."""
        event = CommandEvent(command="  whoami  ")
        self.assertEqual(event.command, "whoami")


class TestImportReport(unittest.TestCase):
    """Tests para ImportReport."""
    
    def test_report_creation(self):
        """Crear un reporte."""
        report = ImportReport()
        self.assertEqual(report.total_lines, 0)
        self.assertEqual(report.imported_commands, 0)
    
    def test_report_success_rate(self):
        """Calcular tasa de éxito."""
        report = ImportReport(total_lines=100, imported_commands=80)
        self.assertEqual(report.success_rate(), 80.0)
    
    def test_report_add_error(self):
        """Agregar errores al reporte."""
        report = ImportReport()
        report.add_error(1, "Test error")
        self.assertEqual(len(report.errors), 1)
        self.assertIn("Line 1", report.errors[0])


class TestPlainTextParser(unittest.TestCase):
    """Tests para parser de texto plano."""
    
    def test_parse_simple_commands(self):
        """Parsear comandos simples."""
        content = "whoami\nls -la\nid"
        parser = PlainTextParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].command, "whoami")
        self.assertEqual(events[1].command, "ls -la")
        self.assertEqual(events[2].command, "id")
        self.assertEqual(report.imported_commands, 3)
    
    def test_parse_with_timestamps(self):
        """Parsear comandos con timestamps."""
        content = "2024-01-15 10:30:45 | whoami\n2024-01-15 10:31:00 | ls -la"
        parser = PlainTextParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)
        self.assertIsNotNone(events[0].timestamp)
        self.assertIsNotNone(events[1].timestamp)
    
    def test_parse_ignore_empty_lines(self):
        """Ignorar líneas vacías."""
        content = "whoami\n\nls -la\n\n\nid"
        parser = PlainTextParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 3)
        self.assertEqual(report.skipped_lines, 3)


class TestJSONParser(unittest.TestCase):
    """Tests para parser JSON."""
    
    def test_parse_json_array(self):
        """Parsear array JSON."""
        content = json.dumps([
            {"command": "whoami", "operator": "admin"},
            {"command": "ls -la", "operator": "admin"}
        ])
        parser = JSONParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].command, "whoami")
        self.assertEqual(events[0].operator, "admin")
    
    def test_parse_json_with_timestamps(self):
        """Parsear JSON con timestamps."""
        content = json.dumps([
            {"command": "whoami", "timestamp": "2024-01-15T10:30:45Z"}
        ])
        parser = JSONParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 1)
        self.assertIsNotNone(events[0].timestamp)
    
    def test_parse_invalid_json(self):
        """Fallar con JSON inválido."""
        content = "{invalid json"
        parser = JSONParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 0)
        self.assertGreater(len(report.errors), 0)


class TestCSVParser(unittest.TestCase):
    """Tests para parser CSV."""
    
    def test_parse_csv(self):
        """Parsear CSV simple."""
        content = "command,operator,user\nwhoami,admin,root\nls -la,admin,root"
        parser = CSVParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].command, "whoami")
        self.assertEqual(events[0].operator, "admin")
    
    def test_parse_csv_with_semicolon(self):
        """Parsear CSV con punto y coma."""
        content = "command;operator\nwhoami;admin\nls -la;admin"
        parser = CSVParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)


class TestBashHistoryParser(unittest.TestCase):
    """Tests para parser Bash History."""
    
    def test_parse_bash_history_with_timestamps(self):
        """Parsear bash history con timestamps."""
        content = "#1705316445\nwhoami\n#1705316460\nls -la"
        parser = BashHistoryParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].command, "whoami")
        self.assertEqual(events[1].command, "ls -la")
    
    def test_parse_bash_history_without_timestamps(self):
        """Parsear bash history sin timestamps."""
        content = "whoami\nls -la\nid"
        parser = BashHistoryParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 3)


class TestZshHistoryParser(unittest.TestCase):
    """Tests para parser Zsh History."""
    
    def test_parse_zsh_history(self):
        """Parsear zsh history."""
        content = ": 1705316445:0;whoami\n: 1705316460:0;ls -la"
        parser = ZshHistoryParser()
        events, report = parser.parse(content)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].command, "whoami")
        self.assertEqual(events[1].command, "ls -la")


class TestLogFormatDetector(unittest.TestCase):
    """Tests para detector de formato."""
    
    def test_detect_json(self):
        """Detectar formato JSON."""
        content = json.dumps([{"command": "whoami"}])
        fmt = LogFormatDetector.detect_format(content)
        self.assertEqual(fmt, "JSON")
    
    def test_detect_csv(self):
        """Detectar formato CSV."""
        content = "command,operator\nwhoami,admin"
        fmt = LogFormatDetector.detect_format(content)
        self.assertEqual(fmt, "CSV")
    
    def test_detect_bash_history(self):
        """Detectar formato Bash History."""
        content = "#1705316445\nwhoami"
        fmt = LogFormatDetector.detect_format(content)
        self.assertEqual(fmt, "BashHistory")
    
    def test_detect_plaintext(self):
        """Detectar formato PlainText."""
        content = "whoami\nls -la"
        fmt = LogFormatDetector.detect_format(content)
        # Podría ser PlainText o algo más, pero no debe ser None
        self.assertIsNotNone(fmt)


class TestLogImporter(unittest.TestCase):
    """Tests para LogImporter (integración)."""
    
    def test_import_from_file_plaintext(self):
        """Importar desde archivo de texto plano."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("whoami\nls -la\nid")
            fname = f.name
        
        try:
            events, report = LogImporter.import_from_file(fname)
            self.assertEqual(len(events), 3)
            self.assertEqual(report.imported_commands, 3)
        finally:
            if os.path.exists(fname):
                os.unlink(fname)
    
    def test_import_from_file_json(self):
        """Importar desde archivo JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"command": "whoami", "operator": "admin"},
                {"command": "ls -la", "operator": "admin"}
            ], f)
            fname = f.name
        
        try:
            events, report = LogImporter.import_from_file(fname)
            self.assertEqual(len(events), 2)
        finally:
            if os.path.exists(fname):
                os.unlink(fname)
    
    def test_import_from_nonexistent_file(self):
        """Fallar si el archivo no existe."""
        events, report = LogImporter.import_from_file("/nonexistent/file.txt")
        self.assertEqual(len(events), 0)
        self.assertGreater(len(report.errors), 0)
    
    def test_import_from_content(self):
        """Importar desde contenido de string."""
        content = "whoami\nls -la"
        events, report = LogImporter.import_from_content(content)
        self.assertEqual(len(events), 2)


class TestLogImportValidator(unittest.TestCase):
    """Tests para LogImportValidator."""
    
    def test_validate_existing_file(self):
        """Validar archivo existente."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            fname = f.name
        
        try:
            valid, msg = LogImportValidator.validate_file(fname)
            self.assertTrue(valid)
            self.assertIsNone(msg)
        finally:
            if os.path.exists(fname):
                os.unlink(fname)
    
    def test_validate_nonexistent_file(self):
        """Validar archivo inexistente."""
        valid, msg = LogImportValidator.validate_file("/nonexistent")
        self.assertFalse(valid)
        self.assertIsNotNone(msg)
    
    def test_validate_empty_file(self):
        """Validar archivo vacío."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        
        try:
            valid, msg = LogImportValidator.validate_file(fname)
            self.assertFalse(valid)
        finally:
            if os.path.exists(fname):
                os.unlink(fname)
    
    def test_validate_supported_format(self):
        """Validar formato soportado."""
        valid, msg = LogImportValidator.validate_format("JSON")
        self.assertTrue(valid)
    
    def test_validate_unsupported_format(self):
        """Validar formato no soportado."""
        valid, msg = LogImportValidator.validate_format("UNKNOWN_FORMAT")
        self.assertFalse(valid)


class TestLogImportManagerIntegration(unittest.TestCase):
    """Tests de integración para LogImportManager."""
    
    def setUp(self):
        """Preparar mocks para CRUD."""
        # Crear un mock simple de CRUD
        class MockCRUD:
            def __init__(self):
                self.actions = []
                self.dao = None
            
            def insert_action(self, action):
                self.actions.append(action)
                return True
            
            def select_all_actions(self):
                return self.actions
        
        self.mock_crud = MockCRUD()
        self.mgr = LogImportManager(crud=self.mock_crud)
    
    def test_import_and_save(self):
        """Importar y guardar eventos en DB."""
        content = "whoami\nls -la"
        imported, report = self.mgr.import_from_content(content)
        
        self.assertGreater(imported, 0)
        self.assertEqual(len(self.mock_crud.actions), 2)
    
    def test_import_sets_report(self):
        """El último reporte está disponible."""
        content = "whoami"
        _, report = self.mgr.import_from_content(content)
        
        last_report = self.mgr.get_last_report()
        self.assertIsNotNone(last_report)
        self.assertEqual(last_report.imported_commands, 1)


if __name__ == '__main__':
    unittest.main()
