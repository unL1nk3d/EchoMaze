"""
LogImporter Module
==================

Módulo principal para importar historiales/logs de comandos en EchoMaze.

Soporta múltiples formatos:
- Texto plano (TXT)
- JSON
- JSON Lines (JSONL)
- CSV
- Bash History
- Zsh History
- PowerShell History
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import re
import csv
from dataclasses import dataclass, field


@dataclass
class CommandEvent:
    """
    Representación normalizada de un evento/comando importado.
    
    Mapea directamente a la entidad Actions de GATHERINGDB.
    """
    command: str
    timestamp: Optional[str] = None
    operator: Optional[str] = None
    user: Optional[str] = None
    shell: Optional[str] = None
    hostname: Optional[str] = None
    exit_code: Optional[int] = None
    description: Optional[str] = None
    source: str = "log_import"  # Origen: log_import, interactive, etc
    import_time: Optional[str] = None  # Momento en que se importó
    
    def __post_init__(self):
        """Validar y limpiar datos."""
        if not self.command or not self.command.strip():
            raise ValueError("Command cannot be empty")
        self.command = self.command.strip()
        if not self.import_time:
            self.import_time = datetime.now().isoformat()


@dataclass
class ImportReport:
    """Reporte de importación con estadísticas y errores."""
    total_lines: int = 0
    imported_commands: int = 0
    skipped_lines: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    format_detected: Optional[str] = None
    
    def add_error(self, line_num: int, msg: str):
        """Agregar error a la lista."""
        self.errors.append(f"Line {line_num}: {msg}")
    
    def add_warning(self, msg: str):
        """Agregar advertencia."""
        self.warnings.append(msg)
    
    def success_rate(self) -> float:
        """Porcentaje de éxito."""
        if self.total_lines == 0:
            return 0.0
        return (self.imported_commands / self.total_lines) * 100
    
    def __str__(self) -> str:
        """Representación en string para mostrar al usuario."""
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"IMPORT REPORT")
        output.append(f"{'='*60}")
        output.append(f"Format Detected: {self.format_detected}")
        output.append(f"Total Lines Processed: {self.total_lines}")
        output.append(f"Imported Commands: {self.imported_commands}")
        output.append(f"Skipped Lines: {self.skipped_lines}")
        output.append(f"Success Rate: {self.success_rate():.1f}%")
        
        if self.warnings:
            output.append(f"\n[!] WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                output.append(f"  - {warn}")
        
        if self.errors:
            output.append(f"\n[ERROR] ERRORS ({len(self.errors)}):")
            for err in self.errors[:10]:  # Show first 10 errors
                output.append(f"  - {err}")
            if len(self.errors) > 10:
                output.append(f"  ... and {len(self.errors) - 10} more errors")
        
        output.append(f"{'='*60}\n")
        return "\n".join(output)


class LogParser(ABC):
    """Clase abstracta para parsers de logs."""
    
    @abstractmethod
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """
        Parsear contenido y retornar eventos + reporte.
        
        Args:
            content: Contenido del archivo
            
        Returns:
            Tupla de (lista de CommandEvent, ImportReport)
        """
        pass
    
    @staticmethod
    def _parse_timestamp(timestamp_str: Optional[str]) -> Optional[str]:
        """
        Intentar parsear timestamp a formato ISO 8601.
        
        Soporta múltiples formatos:
        - ISO 8601: 2024-01-15T10:30:45Z
        - Datetime: 2024-01-15 10:30:45
        - Unix timestamp: 1705316445
        """
        if not timestamp_str:
            return None
        
        timestamp_str = timestamp_str.strip()
        
        # Ya es ISO 8601
        if 'T' in timestamp_str and 'Z' in timestamp_str:
            return timestamp_str
        
        # Intenta como datetime format
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                continue
        
        # Intenta como unix timestamp
        try:
            ts = int(timestamp_str)
            dt = datetime.fromtimestamp(ts)
            return dt.isoformat() + "Z"
        except (ValueError, OSError):
            pass
        
        return None


class PlainTextParser(LogParser):
    """Parser para archivos de texto plano."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear texto plano (un comando por línea)."""
        lines = content.split('\n')
        report = ImportReport(format_detected="PlainText", total_lines=len(lines))
        events = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith('#'):
                report.skipped_lines += 1
                continue
            
            # Intenta parsear timestamp | comando
            match = re.match(r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})\s*[\|:\s]+(.+)$', line)
            
            if match:
                timestamp, command = match.groups()
                timestamp = self._parse_timestamp(timestamp)
            else:
                timestamp = None
                command = line
            
            try:
                event = CommandEvent(
                    command=command,
                    timestamp=timestamp,
                    source="log_import"
                )
                events.append(event)
                report.imported_commands += 1
            except ValueError as e:
                report.add_error(i, str(e))
        
        return events, report


class JSONParser(LogParser):
    """Parser para archivos JSON."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear array JSON de objetos."""
        report = ImportReport(format_detected="JSON")
        events = []
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            report.add_error(0, f"Invalid JSON: {str(e)}")
            return events, report
        
        if not isinstance(data, list):
            report.add_error(0, "JSON root must be an array of objects")
            return events, report
        
        report.total_lines = len(data)
        
        for i, obj in enumerate(data, 1):
            if not isinstance(obj, dict):
                report.add_error(i, "Entry must be an object")
                continue
            
            try:
                command = obj.get('command') or obj.get('cmd')
                if not command:
                    report.add_error(i, "Missing 'command' field")
                    continue
                
                event = CommandEvent(
                    command=command,
                    timestamp=self._parse_timestamp(obj.get('timestamp')),
                    operator=obj.get('operator'),
                    user=obj.get('user'),
                    shell=obj.get('shell'),
                    hostname=obj.get('hostname'),
                    exit_code=obj.get('exit_code'),
                    description=obj.get('description'),
                    source="log_import"
                )
                events.append(event)
                report.imported_commands += 1
            except ValueError as e:
                report.add_error(i, str(e))
        
        return events, report


class JSONLParser(LogParser):
    """Parser para JSON Lines (una línea JSON por comando)."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear JSONL."""
        lines = content.strip().split('\n')
        report = ImportReport(format_detected="JSONL", total_lines=len(lines))
        events = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                report.skipped_lines += 1
                continue
            
            try:
                obj = json.loads(line)
                command = obj.get('command') or obj.get('cmd')
                
                if not command:
                    report.add_error(i, "Missing 'command' field")
                    continue
                
                event = CommandEvent(
                    command=command,
                    timestamp=self._parse_timestamp(obj.get('timestamp')),
                    operator=obj.get('operator'),
                    user=obj.get('user'),
                    shell=obj.get('shell'),
                    hostname=obj.get('hostname'),
                    exit_code=obj.get('exit_code'),
                    description=obj.get('description'),
                    source="log_import"
                )
                events.append(event)
                report.imported_commands += 1
            except json.JSONDecodeError as e:
                report.add_error(i, f"Invalid JSON: {str(e)}")
            except ValueError as e:
                report.add_error(i, str(e))
        
        return events, report


class CSVParser(LogParser):
    """Parser para archivos CSV."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear CSV."""
        report = ImportReport(format_detected="CSV")
        events = []
        
        # Detectar delimitador
        delimiter = self._detect_delimiter(content)
        
        try:
            reader = csv.DictReader(
                content.split('\n'),
                delimiter=delimiter
            )
            
            for i, row in enumerate(reader, 2):  # Línea 2 porque row 1 es header
                if not row or not any(row.values()):
                    report.skipped_lines += 1
                    continue
                
                # Case-insensitive key lookup
                row_lower = {k.lower(): v for k, v in row.items() if k}
                
                try:
                    command = row_lower.get('command') or row_lower.get('cmd')
                    if not command:
                        report.add_error(i, "Missing 'command' column")
                        continue
                    
                    event = CommandEvent(
                        command=command,
                        timestamp=self._parse_timestamp(row_lower.get('timestamp')),
                        operator=row_lower.get('operator'),
                        user=row_lower.get('user'),
                        shell=row_lower.get('shell'),
                        hostname=row_lower.get('hostname'),
                        exit_code=int(row_lower.get('exit_code')) if row_lower.get('exit_code') else None,
                        description=row_lower.get('description'),
                        source="log_import"
                    )
                    events.append(event)
                    report.imported_commands += 1
                except ValueError as e:
                    report.add_error(i, str(e))
            
            report.total_lines = report.imported_commands + report.skipped_lines + len(report.errors)
        
        except Exception as e:
            report.add_error(0, f"CSV parsing failed: {str(e)}")
        
        return events, report
    
    @staticmethod
    def _detect_delimiter(content: str) -> str:
        """Detectar delimitador (coma o punto y coma)."""
        first_line = content.split('\n')[0]
        
        comma_count = first_line.count(',')
        semicolon_count = first_line.count(';')
        
        return ',' if comma_count >= semicolon_count else ';'


class BashHistoryParser(LogParser):
    """Parser para Bash History."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear .bash_history (incluyendo timestamps si existen)."""
        lines = content.split('\n')
        report = ImportReport(format_detected="BashHistory", total_lines=len(lines))
        events = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line:
                report.skipped_lines += 1
                continue
            
            # Línea con timestamp: #<unix_timestamp>
            if line.startswith('#') and line[1:].isdigit():
                timestamp = self._parse_timestamp(line[1:])
                
                # El comando viene en la siguiente línea
                if i < len(lines):
                    command = lines[i].strip()
                    i += 1
                    
                    if command:
                        try:
                            event = CommandEvent(
                                command=command,
                                timestamp=timestamp,
                                source="log_import"
                            )
                            events.append(event)
                            report.imported_commands += 1
                        except ValueError as e:
                            report.add_error(i, str(e))
            else:
                # Comando sin timestamp
                try:
                    event = CommandEvent(
                        command=line,
                        timestamp=None,
                        source="log_import"
                    )
                    events.append(event)
                    report.imported_commands += 1
                except ValueError as e:
                    report.add_error(i, str(e))
        
        return events, report


class ZshHistoryParser(LogParser):
    """Parser para Zsh History con EXTENDED_HISTORY."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear zsh history: : <timestamp>:<elapsed>;<comando>"""
        lines = content.split('\n')
        report = ImportReport(format_detected="ZshHistory", total_lines=len(lines))
        events = []
        
        pattern = r'^:\s*(\d+):(\d+);(.+)$'
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                report.skipped_lines += 1
                continue
            
            match = re.match(pattern, line)
            
            if match:
                timestamp, elapsed, command = match.groups()
                timestamp = self._parse_timestamp(timestamp)
                
                try:
                    event = CommandEvent(
                        command=command,
                        timestamp=timestamp,
                        source="log_import"
                    )
                    events.append(event)
                    report.imported_commands += 1
                except ValueError as e:
                    report.add_error(i, str(e))
            else:
                report.add_error(i, "Does not match zsh history format")
        
        return events, report


class PowerShellHistoryParser(LogParser):
    """Parser para PowerShell History."""
    
    def parse(self, content: str) -> Tuple[List[CommandEvent], ImportReport]:
        """Parsear PowerShell history (texto plano, un comando por línea)."""
        # Para PowerShell, es similar a PlainText
        # pero podría incluir timestamps en formato Windows
        lines = content.split('\n')
        report = ImportReport(format_detected="PowerShellHistory", total_lines=len(lines))
        events = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#'):
                report.skipped_lines += 1
                continue
            
            try:
                event = CommandEvent(
                    command=line,
                    shell="powershell",
                    source="log_import"
                )
                events.append(event)
                report.imported_commands += 1
            except ValueError as e:
                report.add_error(i, str(e))
        
        return events, report


class LogFormatDetector:
    """Detectar automáticamente el formato de un log."""
    
    @staticmethod
    def detect_format(content: str) -> Optional[str]:
        """
        Detectar formato automáticamente.
        
        Returns:
            Nombre del formato detectado o None
        """
        content = content.strip()
        
        if not content:
            return None
        
        # Intenta JSON
        try:
            json.loads(content)
            return "JSON"
        except json.JSONDecodeError:
            pass
        
        # Intenta JSONL
        lines = content.split('\n')
        if all(LogFormatDetector._is_json_line(line.strip()) or not line.strip() 
               for line in lines):
            return "JSONL"
        
        # Intenta CSV (por lo menos 2 líneas y headers)
        if '\n' in content:
            first_line = lines[0]
            if (',' in first_line or ';' in first_line) and 'command' in first_line.lower():
                return "CSV"
        
        # Intenta Bash History
        if any(line.strip().startswith('#') and line.strip()[1:].isdigit() 
               for line in lines[:10]):
            return "BashHistory"
        
        # Intenta Zsh History
        if any(re.match(r'^:\s*\d+:\d+;', line.strip()) for line in lines[:10]):
            return "ZshHistory"
        
        # Por defecto: PlainText
        return "PlainText"
    
    @staticmethod
    def _is_json_line(line: str) -> bool:
        """Verificar si una línea es JSON válido."""
        if not line:
            return True  # Líneas vacías OK
        try:
            json.loads(line)
            return True
        except json.JSONDecodeError:
            return False


class LogImporter:
    """
    Importador principal de logs.
    
    Orquesta detección de formato, parsing y mapeo.
    """
    
    PARSERS = {
        'PlainText': PlainTextParser,
        'JSON': JSONParser,
        'JSONL': JSONLParser,
        'CSV': CSVParser,
        'BashHistory': BashHistoryParser,
        'ZshHistory': ZshHistoryParser,
        'PowerShellHistory': PowerShellHistoryParser,
    }
    
    @staticmethod
    def import_from_file(
        filepath: str,
        format_hint: Optional[str] = None
    ) -> Tuple[List[CommandEvent], ImportReport]:
        """
        Importar comandos desde un archivo.
        
        Args:
            filepath: Ruta al archivo
            format_hint: Formato a usar (auto-detecta si no se especifica)
            
        Returns:
            Tupla de (lista de CommandEvent, ImportReport)
        """
        # Validar archivo
        if not os.path.exists(filepath):
            report = ImportReport(format_detected="ERROR")
            report.add_error(0, f"File not found: {filepath}")
            return [], report
        
        if not os.path.isfile(filepath):
            report = ImportReport(format_detected="ERROR")
            report.add_error(0, f"Not a file: {filepath}")
            return [], report
        
        if not os.access(filepath, os.R_OK):
            report = ImportReport(format_detected="ERROR")
            report.add_error(0, f"Permission denied: {filepath}")
            return [], report
        
        # Leer archivo
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Intenta ISO-8859-1
            try:
                with open(filepath, 'r', encoding='iso-8859-1') as f:
                    content = f.read()
            except Exception as e:
                report = ImportReport(format_detected="ERROR")
                report.add_error(0, f"Cannot read file: {str(e)}")
                return [], report
        except Exception as e:
            report = ImportReport(format_detected="ERROR")
            report.add_error(0, f"Cannot read file: {str(e)}")
            return [], report
        
        # Detectar formato
        if not format_hint:
            format_hint = LogFormatDetector.detect_format(content)
        
        if not format_hint or format_hint not in LogImporter.PARSERS:
            report = ImportReport(format_detected="UNKNOWN")
            report.add_error(0, f"Unknown or unsupported format: {format_hint}")
            return [], report
        
        # Parsear
        parser_class = LogImporter.PARSERS[format_hint]
        parser = parser_class()
        events, report = parser.parse(content)
        
        return events, report
    
    @staticmethod
    def import_from_content(
        content: str,
        format_hint: Optional[str] = None
    ) -> Tuple[List[CommandEvent], ImportReport]:
        """
        Importar comandos desde contenido de texto.
        
        Args:
            content: Contenido del log
            format_hint: Formato a usar (auto-detecta si no se especifica)
            
        Returns:
            Tupla de (lista de CommandEvent, ImportReport)
        """
        if not format_hint:
            format_hint = LogFormatDetector.detect_format(content)
        
        if not format_hint or format_hint not in LogImporter.PARSERS:
            report = ImportReport(format_detected="UNKNOWN")
            report.add_error(0, f"Unknown or unsupported format: {format_hint}")
            return [], report
        
        parser_class = LogImporter.PARSERS[format_hint]
        parser = parser_class()
        events, report = parser.parse(content)
        
        return events, report
