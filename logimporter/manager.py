"""
LogImportManager
================

Gestiona la integración entre LogImporter y GATHERINGDB/Core.

Responsabilidades:
- Valida archivos
- Invoca el LogImporter
- Mapea CommandEvent a Actions (DB)
- Persiste en base de datos
- Reporta al usuario
"""

import os
from typing import List, Tuple, Optional
from datetime import datetime
from GATHERINGDB.model import Actions
from logimporter.importer import LogImporter, CommandEvent, ImportReport


class LogImportManager:
    """
    Gestor de importación de logs integrado con GATHERINGDB.
    """
    
    def __init__(self, crud):
        """
        Inicializar el gestor de importación.
        
        Args:
            crud: Instancia de CRUD_GATHERINGDB
        """
        self.crud = crud
        self.import_report = None
    
    def import_from_file(
        self,
        filepath: str,
        format_hint: Optional[str] = None,
        operator: Optional[str] = None,
        node_id: Optional[int] = None,
        mitre_ttp_id: Optional[str] = None
    ) -> Tuple[int, ImportReport]:
        """
        Importar comandos desde un archivo y guardar en DB.
        
        Args:
            filepath: Ruta al archivo de log
            format_hint: Formato específico (auto-detecta si es None)
            operator: Nombre del operador (opcional)
            node_id: ID del nodo IP asociado (opcional)
            mitre_ttp_id: ID de técnica MITRE (opcional)
            
        Returns:
            Tupla de (cantidad_importada, ImportReport)
        """
        # Importar comandos
        events, report = LogImporter.import_from_file(filepath, format_hint)
        
        if not events:
            self.import_report = report
            return 0, report
        
        self.import_report = report
        
        # Guardar en DB
        saved_count = self._save_events_to_db(
            events,
            operator=operator,
            node_id=node_id,
            mitre_ttp_id=mitre_ttp_id
        )
        
        return saved_count, report
    
    def import_from_content(
        self,
        content: str,
        format_hint: Optional[str] = None,
        operator: Optional[str] = None,
        node_id: Optional[int] = None,
        mitre_ttp_id: Optional[str] = None
    ) -> Tuple[int, ImportReport]:
        """
        Importar comandos desde contenido de texto.
        
        Args:
            content: Contenido del log como string
            format_hint: Formato específico (auto-detecta si es None)
            operator: Nombre del operador (opcional)
            node_id: ID del nodo IP asociado (opcional)
            mitre_ttp_id: ID de técnica MITRE (opcional)
            
        Returns:
            Tupla de (cantidad_importada, ImportReport)
        """
        events, report = LogImporter.import_from_content(content, format_hint)
        
        if not events:
            self.import_report = report
            return 0, report
        
        self.import_report = report
        
        saved_count = self._save_events_to_db(
            events,
            operator=operator,
            node_id=node_id,
            mitre_ttp_id=mitre_ttp_id
        )
        
        return saved_count, report
    
    def _save_events_to_db(
        self,
        events: List[CommandEvent],
        operator: Optional[str] = None,
        node_id: Optional[int] = None,
        mitre_ttp_id: Optional[str] = None
    ) -> int:
        """
        Guardar eventos/comandos en la base de datos.
        
        Mapea CommandEvent a entidad Actions y persiste.
        
        Args:
            events: Lista de eventos a guardar
            operator: Operador por defecto si no viene en evento
            node_id: Node ID por defecto
            mitre_ttp_id: MITRE TTP ID por defecto
            
        Returns:
            Cantidad de eventos guardados exitosamente
        """
        saved = 0
        
        for event in events:
            try:
                # Crear acción desde evento
                action = self._command_event_to_action(
                    event,
                    operator=operator or event.operator,
                    node_id=node_id,
                    mitre_ttp_id=mitre_ttp_id
                )
                
                # Insertar en DB
                if self.crud.insert_action(action):
                    saved += 1
                else:
                    if self.import_report:
                        self.import_report.add_error(
                            0,
                            f"Failed to save command '{event.command}': Database insertion failed"
                        )
            
            except Exception as e:
                # Log error pero continúa con el siguiente evento
                if self.import_report:
                    self.import_report.add_error(
                        0,
                        f"Failed to save command '{event.command}': {str(e)}"
                    )
        
        return saved
    
    @staticmethod
    def _command_event_to_action(
        event: CommandEvent,
        operator: Optional[str] = None,
        node_id: Optional[int] = None,
        mitre_ttp_id: Optional[str] = None
    ) -> Actions:
        """
        Convertir CommandEvent a entidad Actions.
        
        Args:
            event: Evento a convertir
            operator: Operador a usar
            node_id: ID del nodo IP
            mitre_ttp_id: ID de técnica MITRE
            
        Returns:
            Entidad Actions lista para insertar
        """
        action = Actions(
            id=None,  # Auto-generado por DB
            node_id=node_id,
            action_type="imported_command",
            command_template=event.command,
            parameters="",  # Los parámetros están dentro del comando
            mitre_ttp_id=mitre_ttp_id or "",
            timestamp=event.timestamp or event.import_time or datetime.now().isoformat(),
            operator=operator or "unknown",
            noise_score=0.0  # Se calculará después con el scoring engine
        )
        
        return action
    
    def get_last_report(self) -> Optional[ImportReport]:
        """Obtener el último reporte de importación."""
        return self.import_report


class LogImportValidator:
    """
    Validador de archivos y parámetros de importación.
    """
    
    @staticmethod
    def validate_file(filepath: str) -> Tuple[bool, Optional[str]]:
        """
        Validar existencia y permisos de lectura.
        
        Args:
            filepath: Ruta del archivo
            
        Returns:
            Tupla de (válido, mensaje_error_si_hay)
        """
        if not filepath:
            return False, "Filepath cannot be empty"
        
        if not os.path.exists(filepath):
            return False, f"File not found: {filepath}"
        
        if not os.path.isfile(filepath):
            return False, f"Not a file: {filepath}"
        
        if not os.access(filepath, os.R_OK):
            return False, f"Permission denied: {filepath}"
        
        # Validar que no esté vacío
        if os.path.getsize(filepath) == 0:
            return False, "File is empty"
        
        return True, None
    
    @staticmethod
    def validate_format(format_hint: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validar que el formato sea soportado.
        
        Args:
            format_hint: Nombre del formato
            
        Returns:
            Tupla de (válido, mensaje_error_si_hay)
        """
        if not format_hint:
            return True, None  # Auto-detect es válido
        
        supported = [
            'PlainText', 'JSON', 'JSONL', 'CSV',
            'BashHistory', 'ZshHistory', 'PowerShellHistory'
        ]
        
        if format_hint not in supported:
            return False, f"Unsupported format: {format_hint}. Supported: {', '.join(supported)}"
        
        return True, None


def validate_import_params(
    filepath: str,
    format_hint: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Función de conveniencia para validar parámetros de importación.
    
    Args:
        filepath: Ruta del archivo
        format_hint: Formato a usar
        
    Returns:
        Tupla de (válido, mensaje_error_si_hay)
    """
    valid, msg = LogImportValidator.validate_file(filepath)
    if not valid:
        return False, msg
    
    valid, msg = LogImportValidator.validate_format(format_hint)
    if not valid:
        return False, msg
    
    return True, None
