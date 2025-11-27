import os
from typing import Generator, List
from GATHERINGDB.dao import GenericDAO, Transaction
from GATHERINGDB.model import Actions, Mitre_attack, Artifacts, Opsec_logs, IPNode,Templates
from GATHERINGDB.log import log


class CRUD_Template:
    def __init__(self, dao: GenericDAO = None):
        self.dao = dao

    def insert_template(self, technique: str, name: str, desc: str,
                        linux: str, windows: str, noise_estimate: float = 0.0,
                        dao: GenericDAO = None) -> Templates:
        """Insertar un template nuevo"""
        try:
            _dao = dao or self.dao
            tpl = Templates(technique, name, desc, linux, windows, noise_estimate)
            _dao.insertar(tpl)
            log.info(f"[+] Template inserted: {technique}")
            return tpl
        except Exception as e:
            log.error(f"[-] Error inserting template {technique}: {e}")
            raise

    def select_all_templates(self, dao: GenericDAO = None) -> List[Templates]:
        """Devolver todos los templates"""
        try:
            _dao = dao or self.dao
            return _dao.seleccionar(Templates)
        except Exception as e:
            log.error(f"[-] Error selecting templates: {e}")
            return []

    def select_template_by_technique(self, technique: str, dao: GenericDAO = None) -> Templates | None:
        """Buscar template por su técnica (clave)"""
        try:
            _dao = dao or self.dao
            templates = _dao.seleccionar(Templates)
            return next((t for t in templates if getattr(t, "technique", None) == technique), None)
        except Exception as e:
            log.error(f"[-] Error selecting template {technique}: {e}")
            return None

    def update_template(self, technique: str, name: str = None, desc: str = None,
                        linux: str = None, windows: str = None, noise_estimate: float = None,
                        dao: GenericDAO = None) -> Templates:
        """Actualizar campos de un template existente"""
        try:
            _dao = dao or self.dao
            tpl = self.select_template_by_technique(technique, dao=_dao)
            if not tpl:
                raise ValueError(f"No template found with technique {technique}")
            if name is not None:
                tpl.name = name
            if desc is not None:
                tpl.desc = desc
            if linux is not None:
                tpl.linux = linux
            if windows is not None:
                tpl.windows = windows
            if noise_estimate is not None:
                tpl.noise_estimate = noise_estimate
            _dao.actualizar(tpl, technique)
            log.info(f"[+] Template {technique} updated")
            return tpl
        except Exception as e:
            log.error(f"[-] Error updating template {technique}: {e}")
            raise

    def delete_template(self, technique: str, dao: GenericDAO = None):
        """Eliminar un template por técnica"""
        try:
            _dao = dao or self.dao
            tpl = self.select_template_by_technique(technique, dao=_dao)
            if not tpl:
                raise ValueError(f"No template found with technique {technique}")
            _dao.eliminar(tpl, technique)
            log.info(f"[+] Template {technique} deleted")
        except Exception as e:
            log.error(f"[-] Error deleting template {technique}: {e}")
            raise

class CRUD_ACTIONS:
    def insert_action(self, node_id: int, action_type: str, command_template: str,
                     parameters: str, mitre_ttp_id: str, operator: str,
                     noise_score: float = 0.0, dao: GenericDAO = None) -> Actions:
        """Insertar una nueva acción"""
        try:
            # Validar que el nodo existe
            node = dao.seleccionarPorId(IPNode, node_id)
            if not node:
                raise ValueError(f"No IPNode found with id {node_id}")
            
            action = Actions(
                id=0,
                node_id=node_id,
                action_type=action_type,
                command_template=command_template,
                parameters=parameters,
                mitre_ttp_id=mitre_ttp_id,
                timestamp="",  # se asigna en BD por defecto
                operator=operator,
                noise_score=noise_score
            )
            dao.insertar(action)
            log.info(f"[+] Action inserted: {action_type} for node {node_id}")
            return action
        except Exception as e:
            log.error(f"[-] Error inserting action: {e}")
            raise

    def select_all_actions(self, dao: GenericDAO = None) -> List[Actions]:
        """Obtener todas las acciones"""
        try:
            return dao.seleccionar(Actions)
        except Exception as e:
            log.error(f"[-] Error selecting actions: {e}")
            return []

    def select_actions_by_node(self, node_id: int, dao: GenericDAO = None) -> List[Actions]:
        """Obtener todas las acciones de un nodo específico"""
        try:
            # Usar selectCoincidence si está disponible, sino filtrar manualmente
            actions = dao.seleccionar(Actions)
            return [a for a in actions if a.node_id == node_id]
        except Exception as e:
            log.error(f"[-] Error selecting actions by node {node_id}: {e}")
            return []

    def select_actions_by_mitre_ttp(self, mitre_ttp_id: str, dao: GenericDAO = None) -> List[Actions]:
        """Obtener acciones asociadas a un MITRE TTP específico"""
        try:
            actions = dao.seleccionar(Actions)
            return [a for a in actions if a.mitre_ttp_id == mitre_ttp_id]
        except Exception as e:
            log.error(f"[-] Error selecting actions by MITRE TTP {mitre_ttp_id}: {e}")
            return []

    def update_action(self, action_id: int, action_type: str = None, command_template: str = None,
                     parameters: str = None, noise_score: float = None, dao: GenericDAO = None):
        """Actualizar una acción existente"""
        try:
            actions = dao.seleccionar(Actions)
            action = next((a for a in actions if a.id == action_id), None)
            if not action:
                raise ValueError(f"No Action found with id {action_id}")
            
            # Actualizar solo los campos proporcionados
            if action_type:
                action.action_type = action_type
            if command_template:
                action.command_template = command_template
            if parameters:
                action.parameters = parameters
            if noise_score is not None:
                action.noise_score = noise_score
            
            dao.actualizar(action, action_id)
            log.info(f"[+] Action {action_id} updated")
        except Exception as e:
            log.error(f"[-] Error updating action {action_id}: {e}")
            raise

    def delete_action(self, action_id: int, dao: GenericDAO = None):
        """Eliminar una acción"""
        try:
            actions = dao.seleccionar(Actions)
            action = next((a for a in actions if a.id == action_id), None)
            if not action:
                raise ValueError(f"No Action found with id {action_id}")
            
            dao.eliminar(action, action_id)
            log.info(f"[+] Action {action_id} deleted")
        except Exception as e:
            log.error(f"[-] Error deleting action {action_id}: {e}")
            raise
class CRUD_OPSEC:
    def insert_opsec_log(self, action_id: int, event: str, severity: int,
                        details: str = "", dao: GenericDAO = None) -> Opsec_logs:
        """Insertar un nuevo registro OPSEC"""
        try:
            # Validar que la acción existe
            actions = dao.seleccionar(Actions)
            action = next((a for a in actions if a.id == action_id), None)
            if not action:
                raise ValueError(f"No Action found with id {action_id}")
            
            log_entry = Opsec_logs(
                id=0,
                action_id=action_id,
                event=event,
                severity=severity,
                details=details,
                created_at=""  # se asigna en BD por defecto
            )
            dao.insertar(log_entry)
            log.info(f"[+] OPSEC log inserted for action {action_id}")
            return log_entry
        except Exception as e:
            log.error(f"[-] Error inserting OPSEC log: {e}")
            raise

    def select_all_opsec_logs(self, dao: GenericDAO = None) -> List[Opsec_logs]:
        """Obtener todos los registros OPSEC"""
        try:
            return dao.seleccionar(Opsec_logs)
        except Exception as e:
            log.error(f"[-] Error selecting OPSEC logs: {e}")
            return []

    def select_opsec_logs_by_action(self, action_id: int, dao: GenericDAO = None) -> List[Opsec_logs]:
        """Obtener registros OPSEC de una acción específica"""
        try:
            logs = dao.seleccionar(Opsec_logs)
            return [l for l in logs if l.action_id == action_id]
        except Exception as e:
            log.error(f"[-] Error selecting OPSEC logs by action {action_id}: {e}")
            return []

    def select_opsec_logs_by_severity(self, severity: int, dao: GenericDAO = None) -> List[Opsec_logs]:
        """Obtener registros OPSEC por severidad"""
        try:
            logs = dao.seleccionar(Opsec_logs)
            return [l for l in logs if l.severity == severity]
        except Exception as e:
            log.error(f"[-] Error selecting OPSEC logs by severity {severity}: {e}")
            return []

    def update_opsec_log(self, log_id: int, event: str = None, severity: int = None,
                        details: str = None, dao: GenericDAO = None):
        """Actualizar un registro OPSEC"""
        try:
            logs = dao.seleccionar(Opsec_logs)
            log_entry = next((l for l in logs if l.id == log_id), None)
            if not log_entry:
                raise ValueError(f"No OPSEC log found with id {log_id}")
            
            if event:
                log_entry.event = event
            if severity is not None:
                log_entry.severity = severity
            if details:
                log_entry.details = details
            
            dao.actualizar(log_entry, log_id)
            log.info(f"[+] OPSEC log {log_id} updated")
        except Exception as e:
            log.error(f"[-] Error updating OPSEC log {log_id}: {e}")
            raise

    def delete_opsec_log(self, log_id: int, dao: GenericDAO = None):
        """Eliminar un registro OPSEC"""
        try:
            logs = dao.seleccionar(Opsec_logs)
            log_entry = next((l for l in logs if l.id == log_id), None)
            if not log_entry:
                raise ValueError(f"No OPSEC log found with id {log_id}")
            
            dao.eliminar(log_entry, log_id)
            log.info(f"[+] OPSEC log {log_id} deleted")
        except Exception as e:
            log.error(f"[-] Error deleting OPSEC log {log_id}: {e}")
            raise
class CRUD_ARTIFACTS:
    def insert_artifact(self, filename: str, node_id: int, sha1: str = "",
                       sha256: str = "", md5: str = "", size: int = 0,
                       notes: str = "", dao: GenericDAO = None) -> Artifacts:
        """Insertar un nuevo artefacto"""
        try:
            # Validar que el nodo existe
            node = dao.seleccionarPorId(IPNode, node_id)
            if not node:
                raise ValueError(f"No IPNode found with id {node_id}")
            
            artifact = Artifacts(
                id=0,
                filename=filename,
                node_id=node_id,
                sha1=sha1,
                sha256=sha256,
                md5=md5,
                size=size,
                created_at="",  # se asigna en BD por defecto
                notes=notes
            )
            dao.insertar(artifact)
            log.info(f"[+] Artifact inserted: {filename} for node {node_id}")
            return artifact
        except Exception as e:
            log.error(f"[-] Error inserting artifact: {e}")
            raise

    def select_all_artifacts(self, dao: GenericDAO = None) -> List[Artifacts]:
        """Obtener todos los artefactos"""
        try:
            return dao.seleccionar(Artifacts)
        except Exception as e:
            log.error(f"[-] Error selecting artifacts: {e}")
            return []

    def select_artifacts_by_node(self, node_id: int, dao: GenericDAO = None) -> List[Artifacts]:
        """Obtener artefactos de un nodo específico"""
        try:
            artifacts = dao.seleccionar(Artifacts)
            return [a for a in artifacts if a.node_id == node_id]
        except Exception as e:
            log.error(f"[-] Error selecting artifacts by node {node_id}: {e}")
            return []

    def select_artifact_by_hash(self, hash_value: str, dao: GenericDAO = None) -> List[Artifacts]:
        """Obtener artefactos por hash (SHA1, SHA256 o MD5)"""
        try:
            artifacts = dao.seleccionar(Artifacts)
            return [a for a in artifacts if a.sha1 == hash_value or a.sha256 == hash_value or a.md5 == hash_value]
        except Exception as e:
            log.error(f"[-] Error selecting artifact by hash: {e}")
            return []

    def update_artifact(self, artifact_id: int, filename: str = None, sha1: str = None,
                       sha256: str = None, md5: str = None, size: int = None,
                       notes: str = None, dao: GenericDAO = None):
        """Actualizar un artefacto"""
        try:
            artifacts = dao.seleccionar(Artifacts)
            artifact = next((a for a in artifacts if a.id == artifact_id), None)
            if not artifact:
                raise ValueError(f"No Artifact found with id {artifact_id}")
            
            if filename:
                artifact.filename = filename
            if sha1:
                artifact.sha1 = sha1
            if sha256:
                artifact.sha256 = sha256
            if md5:
                artifact.md5 = md5
            if size is not None:
                artifact.size = size
            if notes:
                artifact.notes = notes
            
            dao.actualizar(artifact, artifact_id)
            log.info(f"[+] Artifact {artifact_id} updated")
        except Exception as e:
            log.error(f"[-] Error updating artifact {artifact_id}: {e}")
            raise

    def delete_artifact(self, artifact_id: int, dao: GenericDAO = None):
        """Eliminar un artefacto"""
        try:
            artifacts = dao.seleccionar(Artifacts)
            artifact = next((a for a in artifacts if a.id == artifact_id), None)
            if not artifact:
                raise ValueError(f"No Artifact found with id {artifact_id}")
            
            dao.eliminar(artifact, artifact_id)
            log.info(f"[+] Artifact {artifact_id} deleted")
        except Exception as e:
            log.error(f"[-] Error deleting artifact {artifact_id}: {e}")
            raise
class CRUD_MITRE:
    """
    CRUD especializado para modelos de MITRE ATT&CK, Acciones, Artefactos y Logs OPSEC.
    Maneja operaciones CRUD para:
    - Actions: acciones ejecutadas contra nodos
    - Mitre_attack: base de datos de tácticas y técnicas MITRE
    - Artifacts: archivos y artefactos recolectados
    - Opsec_logs: registros de eventos OPSEC
    """

    def __init__(self, dao: GenericDAO = None):
        self.dao = dao

    # ============================================================================
    # ACTIONS CRUD
    # ============================================================================


    # ============================================================================
    # MITRE_ATTACK CRUD
    # ============================================================================

    def insert_mitre_ttp(self, mitre_id: str, tactic: str, technique: str,
                        description: str, dao: GenericDAO = None) -> Mitre_attack:
        """Insertar una nueva técnica/táctica MITRE"""
        try:
            mitre_entry = Mitre_attack(
                mitre_id=mitre_id,
                tactic=tactic,
                technique=technique,
                description=description
            )
            dao.insertar(mitre_entry)
            log.info(f"[+] MITRE TTP inserted: {mitre_id}")
            return mitre_entry
        except Exception as e:
            log.error(f"[-] Error inserting MITRE TTP: {e}")
            raise

    def select_all_mitre_ttps(self, dao: GenericDAO = None) -> List[Mitre_attack]:
        """Obtener todas las técnicas MITRE"""
        try:
            return dao.seleccionar(Mitre_attack)
        except Exception as e:
            log.error(f"[-] Error selecting MITRE TTPs: {e}")
            return []

    def select_mitre_by_id(self, mitre_id: str, dao: GenericDAO = None) -> Mitre_attack:
        """Obtener una técnica MITRE por ID"""
        try:
            mitre_entries = dao.seleccionar(Mitre_attack)
            return next((m for m in mitre_entries if m.mitre_id == mitre_id), None)
        except Exception as e:
            log.error(f"[-] Error selecting MITRE TTP by id {mitre_id}: {e}")
            return None

    def select_mitre_by_tactic(self, tactic: str, dao: GenericDAO = None) -> List[Mitre_attack]:
        """Obtener técnicas MITRE por táctica"""
        try:
            mitre_entries = dao.seleccionar(Mitre_attack)
            return [m for m in mitre_entries if m.tactic.lower() == tactic.lower()]
        except Exception as e:
            log.error(f"[-] Error selecting MITRE TTPs by tactic {tactic}: {e}")
            return []

    def update_mitre_ttp(self, mitre_id: str, tactic: str = None, technique: str = None,
                        description: str = None, dao: GenericDAO = None):
        """Actualizar una técnica MITRE"""
        try:
            mitre_entries = dao.seleccionar(Mitre_attack)
            mitre_entry = next((m for m in mitre_entries if m.mitre_id == mitre_id), None)
            if not mitre_entry:
                raise ValueError(f"No MITRE TTP found with id {mitre_id}")
            
            if tactic:
                mitre_entry.tactic = tactic
            if technique:
                mitre_entry.technique = technique
            if description:
                mitre_entry.description = description
            
            dao.actualizar(mitre_entry, mitre_id)
            log.info(f"[+] MITRE TTP {mitre_id} updated")
        except Exception as e:
            log.error(f"[-] Error updating MITRE TTP {mitre_id}: {e}")
            raise

    def delete_mitre_ttp(self, mitre_id: str, dao: GenericDAO = None):
        """Eliminar una técnica MITRE"""
        try:
            mitre_entries = dao.seleccionar(Mitre_attack)
            mitre_entry = next((m for m in mitre_entries if m.mitre_id == mitre_id), None)
            if not mitre_entry:
                raise ValueError(f"No MITRE TTP found with id {mitre_id}")
            
            dao.eliminar(mitre_entry, mitre_id)
            log.info(f"[+] MITRE TTP {mitre_id} deleted")
        except Exception as e:
            log.error(f"[-] Error deleting MITRE TTP {mitre_id}: {e}")
            raise

    # ============================================================================
    # ARTIFACTS CRUD
    # ============================================================================


    # ============================================================================
    # OPSEC_LOGS CRUD
    # ============================================================================




def main():
    """Ejemplo de uso del CRUD MITRE"""
    from GATHERINGDB.init_db import DatabaseInitializer
    
    dao = GenericDAO()
    crud_mitre = CRUD_MITRE(dao)
    
    # Insertar una técnica MITRE
    mitre_ttp = crud_mitre.insert_mitre_ttp(
        "T1046",
        "Discovery",
        "Network Service Discovery",
        "Adversaries may attempt to get a listing of services running on remote hosts.",
        dao=dao
    )
    
    # Insertar una acción
    action = crud_mitre.insert_action(
        node_id=1,
        action_type="nmap_scan",
        command_template="nmap -sV {target}",
        parameters='{"target": "192.168.1.100"}',
        mitre_ttp_id="T1046",
        operator="analyst1",
        noise_score=0.3,
        dao=dao
    )
    
    # Insertar un artefacto
    artifact = crud_mitre.insert_artifact(
        filename="scan_results.xml",
        node_id=1,
        sha256="abc123def456...",
        size=2048,
        notes="nmap scan results",
        dao=dao
    )
    
    # Insertar un registro OPSEC
    opsec_log = crud_mitre.insert_opsec_log(
        action_id=action.id,
        event="scan_completed",
        severity=2,
        details="Network scan completed successfully",
        dao=dao
    )
    
    # Mostrar datos
    print("\n[+] All MITRE TTPs:")
    for ttp in crud_mitre.select_all_mitre_ttps(dao=dao):
        print(f"  {ttp.mitre_id}: {ttp.technique}")
    
    print("\n[+] All Actions:")
    for act in crud_mitre.select_all_actions(dao=dao):
        print(f"  {act.action_type} for node {act.node_id}")
    
    print("\n[+] All Artifacts:")
    for art in crud_mitre.select_all_artifacts(dao=dao):
        print(f"  {art.filename} (SHA256: {art.sha256[:10]}...)")
    
    print("\n[+] All OPSEC Logs:")
    for log_entry in crud_mitre.select_all_opsec_logs(dao=dao):
        print(f"  [{log_entry.severity}] {log_entry.event}: {log_entry.details}")


if __name__ == '__main__':
    DatabaseInitializer.initialize_db(dao=GenericDAO())
    main()