"""
LogImporter Package
===================

Módulo para importar historiales/logs de comandos en EchoMaze.

Expone:
- LogImporter: Clase principal para importación
- LogImportManager: Gestor integrado con GATHERINGDB
- CommandEvent: Modelo normalizado de eventos
- ImportReport: Reporte de importación
"""

from logimporter.importer import (
    LogImporter,
    CommandEvent,
    ImportReport,
    LogFormatDetector
)

from logimporter.manager import (
    LogImportManager,
    LogImportValidator,
    validate_import_params
)

__all__ = [
    'LogImporter',
    'CommandEvent',
    'ImportReport',
    'LogFormatDetector',
    'LogImportManager',
    'LogImportValidator',
    'validate_import_params'
]
