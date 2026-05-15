from dataclasses import dataclass
import sqlite3

class IntegrityError(Exception):
    def __init__(self, datatype: str, *args):
        super().__init__("Integrity error on table {datatype}".format(datatype=datatype), *args)

class TransitiveTable:
    @classmethod
    def create_table(cls) -> str:
        ...

class BaseEntity:
    @classmethod
    def select_map(cls):
        return {}
    @classmethod
    def insert(cls):
        ...
    @classmethod
    def update(cls):
        ...
    @classmethod
    def delete(cls):
        ...
    @classmethod
    def get_guid() -> str:
        raise NotImplementedError("Subclasses must implement get_guid method")
    def exportAsTupple(self) -> tuple:
        raise NotImplementedError("Subclasses must implement exportAsTupple method")
    @classmethod
    def create_table() -> str:
        raise NotImplementedError("Subclasses must implement create_table method")
    @classmethod
    def select(cls) -> str:
        raise NotImplementedError("Subclasses must implement select method")
    @classmethod
    def selectById(cls) -> str:
        raise NotImplementedError("Subclasses must implement selectById method")
    @classmethod
    def selectCoincidence(cls) -> str:
        raise NotImplementedError("Subclasses must implement selectCoincidence method")

@dataclass
class IPNode(BaseEntity):
    id: int
    ip: str
    path: str
    parent_ip: str = None
    child_level: int = 0
    score: float = 0.0  # Score for noise/visibility
    opsec_flag: int = 0  # 0/1 for False/True (OPSEC concern)

    @classmethod
    def get_guid(cls):
        return 'ip'
    @classmethod
    def insert(cls):
        return f"INSERT INTO ip_node(ip,path,parent_ip,child_level,score,opsec_flag) VALUES (?,?,?,?,?,?)"
    @classmethod
    def update(cls):
        return f"UPDATE ip_node SET ip=?, path=?, parent_ip=?, child_level=?, score=?, opsec_flag=? WHERE id=?"
    @classmethod
    def delete(cls):
        return f"DELETE FROM ip_node WHERE id=?"
    def exportAsTupple(self):
        return (self.ip, self.path, self.parent_ip, self.child_level, self.score, self.opsec_flag)
    @classmethod
    def select(cls):
        return "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node"
    @classmethod
    def selectById(cls):
        return "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node WHERE id=?"
    @classmethod
    def select_map(cls):
        sm = {
            "ip": "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node WHERE ip = ?",
            "id": "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node WHERE id = ?",
            "parent_ip": "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node WHERE parent_ip = ?",
            "child_level": "SELECT id, ip, path, parent_ip, child_level, score, opsec_flag FROM ip_node WHERE child_level = ?",
            "max_child_level_by_parent": "SELECT MAX(child_level) as max_level FROM ip_node where parent_ip = ?"
        }
        return sm
    @classmethod
    def selectCoincidence(cls, field):
        sm = cls.select_map().get(field, None)
        if not sm:
            raise ValueError(f"No se definio una consulta de tipo {field} en {cls.__name__} ")
        return sm
    @classmethod
    def create_table(cls):
        return '''
            CREATE TABLE IF NOT EXISTS ip_node (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                path TEXT NOT NULL,
                parent_ip TEXT,
                child_level INTEGER DEFAULT 0,
                score REAL DEFAULT 0.0,
                opsec_flag INTEGER DEFAULT 0
            )
        '''

@dataclass
class Ports(BaseEntity):
    id: int
    port: int
    service_name: str
    ip: str
    @classmethod
    def get_guid(cls):
        return 'port'
    @classmethod
    def insert(cls):
        return f"INSERT INTO ports(port,service_name,ip) VALUES (?,?,?)"
    @classmethod
    def update(cls):
        return f"UPDATE ports SET port=?, service_name=?,ip=? WHERE id=?"
    @classmethod
    def delete(cls):
        return f"DELETE FROM ports WHERE id=?"
    @classmethod
    def select(cls):
        return f"SELECT id, port, service_name, ip FROM ports"
    @classmethod
    def selectById(cls):
        return f"SELECT id, port, service_name, ip FROM ports WHERE id=?"
    @classmethod
    def select_map(cls):
        sm = {
            "ip": "SELECT id, port, service_name,ip FROM ports WHERE  ip = ?",
            "id": "SELECT id, port, service_name,ip FROM ports WHERE  id = ?"
        }
        return sm
    @classmethod
    def selectCoincidence(cls, field):
        sm = cls.select_map().get(field, None)
        if not sm:
            raise ValueError(f"No se definio una consulta de tipo {field} en {cls.__name__} ")
        return sm
    def exportAsTupple(self):
        return (self.port, self.service_name, self.ip)
    @classmethod
    def create_table(cls):
        return '''
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                ip TEXT NOT NULL,
                FOREIGN KEY(ip) REFERENCES ip_node(ip)
            )
        '''

# NUEVAS ENTIDADES BLOQUE 1
@dataclass
class WorkflowScoreConfig(BaseEntity):
    """
    Represents workflow scoring configuration parameters.
    """
    id: int
    name: str
    value: float
    description: str = ""

    @classmethod
    def get_guid(cls):
        return "id"
    @classmethod
    def insert(cls):
        return "INSERT INTO workflow_score_config(name, value, description) VALUES (?, ?, ?)"
    @classmethod
    def update(cls):
        return "UPDATE workflow_score_config SET name=?, value=?, description=? WHERE id=?"
    @classmethod
    def delete(cls):
        return "DELETE FROM workflow_score_config WHERE id=?"
    def exportAsTupple(self):
        return (self.name, self.value, self.description)
    @classmethod
    def select(cls):
        return "SELECT id, name, value, description FROM workflow_score_config"
    @classmethod
    def selectById(cls):
        return "SELECT id, name, value, description FROM workflow_score_config WHERE id=?"
    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT id, name, value, description FROM workflow_score_config WHERE {field}=?"
    @classmethod
    def create_table(cls):
        return """
        CREATE TABLE IF NOT EXISTS workflow_score_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            description TEXT
        )
        """

@dataclass
class PivotHistory(BaseEntity):
    """
    Represents a history entry for a pivot operation between hosts.
    """
    id: int
    source_ip: str
    dest_ip: str
    operator: str
    timestamp: str
    details: str = ""

    @classmethod
    def get_guid(cls):
        return "id"
    @classmethod
    def insert(cls):
        return "INSERT INTO pivot_history(source_ip, dest_ip, operator, timestamp, details) VALUES (?, ?, ?, ?, ?)"
    @classmethod
    def update(cls):
        return "UPDATE pivot_history SET source_ip=?, dest_ip=?, operator=?, timestamp=?, details=? WHERE id=?"
    @classmethod
    def delete(cls):
        return "DELETE FROM pivot_history WHERE id=?"
    def exportAsTupple(self):
        return (self.source_ip, self.dest_ip, self.operator, self.timestamp, self.details)
    @classmethod
    def select(cls):
        return "SELECT id, source_ip, dest_ip, operator, timestamp, details FROM pivot_history"
    @classmethod
    def selectById(cls):
        return "SELECT id, source_ip, dest_ip, operator, timestamp, details FROM pivot_history WHERE id=?"
    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT id, source_ip, dest_ip, operator, timestamp, details FROM pivot_history WHERE {field}=?"
    @classmethod
    def create_table(cls):
        return """
        CREATE TABLE IF NOT EXISTS pivot_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT NOT NULL,
            dest_ip TEXT NOT NULL,
            operator TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT
        )
        """

# ... el resto del modelo y entidades no cambia del archivo original ...



@dataclass
class Actions(BaseEntity):
    # -- Historico de acciones / comandos sugeridos / ejecutados
    # aka procediments knowed on the MITRE 
    id: int
    node_id: int
    action_type: str
    command_template: str
    # es un comando a ejecutar por ejemplo kerbrute.exe
    parameters: str
    # descripcion de cada parametro en formato JSON
    # dict[str,str] ejemplo:
    # {"-L":"LOCAL LISTEN"}
    mitre_ttp_id: str
    # relacion con algun ttp del mitre
    timestamp: str
    operator: str
    # nombre del operador que realizo la accion
    noise_score: float

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.node_id, self.action_type, self.command_template, self.parameters,
                self.mitre_ttp_id, self.timestamp, self.operator, self.noise_score)

    @classmethod
    def insert(cls):
        return """INSERT INTO actions 
            (node_id, action_type, command_template, parameters, mitre_ttp_id, timestamp, operator, noise_score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id INTEGER,
            action_type TEXT,
            command_template TEXT,
            parameters TEXT,
            mitre_ttp_id TEXT,
            timestamp TIMESTAMP DEFAULT (datetime('now')),
            operator TEXT,
            noise_score REAL DEFAULT 0,
            FOREIGN KEY(node_id) REFERENCES ip_node(id)
        );"""

    @classmethod
    def select(cls):
        return "SELECT * FROM actions;"

    @classmethod
    def selectById(cls):
        return "SELECT * FROM actions WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT * FROM {cls.__name__.lower()} WHERE {field} = ?;"

@dataclass
class Mitre_attack(BaseEntity):
    mitre_id: str
    tactic: str
    technique: str
    description: str

    @classmethod
    def get_guid(cls):
        return "mitre_id"

    def exportAsTupple(self):
        return (self.mitre_id, self.tactic, self.technique, self.description)

    @classmethod
    def insert(cls):
        return "INSERT INTO mitre_attack (mitre_id, tactic, technique, description) VALUES (?, ?, ?, ?)"

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS mitre_attack (
            mitre_id TEXT PRIMARY KEY,
            tactic TEXT,
            technique TEXT,
            description TEXT
        );"""

    @classmethod
    def select(cls):
        return "SELECT * FROM mitre_attack;"

    @classmethod
    def selectById(cls):
        return "SELECT * FROM mitre_attack WHERE mitre_id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT * FROM {cls.__name__.lower()} WHERE {field} = ?;"

@dataclass
class Artifacts(BaseEntity):
    id: int
    filename: str
    node_id: int
    sha1: str
    sha256: str
    md5: str
    size: int
    created_at: str
    notes: str
    noise_score: float

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.filename, self.node_id, self.sha1, self.sha256, self.md5,
                self.size, self.notes, self.noise_score)

    @classmethod
    def insert(cls):
        return """INSERT INTO artifacts 
            (filename, node_id, sha1, sha256, md5, size, notes, noise_score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            node_id INTEGER,
            sha1 TEXT,
            sha256 TEXT,
            md5 TEXT,
            size INTEGER,
            created_at TIMESTAMP DEFAULT (datetime('now')),
            notes TEXT,
            noise_score REAL DEFAULT 0.0,
            FOREIGN KEY(node_id) REFERENCES ip_node(id)
        );"""

    @classmethod
    def select(cls):
        return "SELECT * FROM artifacts;"

    @classmethod
    def selectById(cls):
        return "SELECT * FROM artifacts WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT * FROM {cls.__name__.lower()} WHERE {field} = ?;"


@dataclass
class Opsec_logs(BaseEntity):
    id: int
    action_id: int
    event: str
    severity: int
    details: str
    created_at: str

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.action_id, self.event, self.severity, self.details)

    @classmethod
    def insert(cls):
        return """INSERT INTO opsec_logs 
            (action_id, event, severity, details) 
            VALUES (?, ?, ?, ?)"""

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS opsec_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER,
            event TEXT,
            severity INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now')),
            FOREIGN KEY(action_id) REFERENCES actions(id)
        );"""

    @classmethod
    def select(cls):
        return "SELECT * FROM opsec_logs;"

    @classmethod
    def selectById(cls):
        return "SELECT * FROM opsec_logs WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT * FROM opsec_logs WHERE {field} = ?;"



@dataclass
class TunnelDB(BaseEntity):
    """
    Represents a network tunnel persisted in the database.
    """
    id: int
    source_ip: str
    dest_ip: str
    local_port: int
    remote_port: int
    status: str
    technique: str
    phase: str
    tunnel_type: str
    data_sent_bytes: int
    data_received_bytes: int
    last_activity: str
    entropy_score: float
    entropy_warning: str
    data_type: str = "texto plano"
    implant_id: int = None

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.source_ip, self.dest_ip, self.local_port, self.remote_port,
                self.status, self.technique, self.phase, self.tunnel_type,
                self.data_sent_bytes, self.data_received_bytes, self.last_activity,
                self.entropy_score, self.entropy_warning, self.data_type, self.implant_id)

    @classmethod
    def insert(cls):
        return """INSERT INTO tunnels 
            (source_ip, dest_ip, local_port, remote_port, status, technique, phase, 
             tunnel_type, data_sent_bytes, data_received_bytes, last_activity, 
             entropy_score, entropy_warning, data_type, implant_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    @classmethod
    def update(cls):
        return """UPDATE tunnels SET 
            source_ip=?, dest_ip=?, local_port=?, remote_port=?, status=?, 
            technique=?, phase=?, tunnel_type=?, data_sent_bytes=?, 
            data_received_bytes=?, last_activity=?, entropy_score=?, 
            entropy_warning=?, data_type=?, implant_id=? WHERE id=?"""

    @classmethod
    def delete(cls):
        return "DELETE FROM tunnels WHERE id=?"

    @classmethod
    def select(cls):
        return "SELECT id, source_ip, dest_ip, local_port, remote_port, status, technique, phase, tunnel_type, data_sent_bytes, data_received_bytes, last_activity, entropy_score, entropy_warning, data_type, implant_id FROM tunnels;"

    @classmethod
    def selectById(cls):
        return "SELECT id, source_ip, dest_ip, local_port, remote_port, status, technique, phase, tunnel_type, data_sent_bytes, data_received_bytes, last_activity, entropy_score, entropy_warning, data_type, implant_id FROM tunnels WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT id, source_ip, dest_ip, local_port, remote_port, status, technique, phase, tunnel_type, data_sent_bytes, data_received_bytes, last_activity, entropy_score, entropy_warning, data_type, implant_id FROM tunnels WHERE {field} = ?;"

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS tunnels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ip TEXT NOT NULL,
            dest_ip TEXT,
            local_port INTEGER,
            remote_port INTEGER,
            status TEXT,
            technique TEXT,
            phase TEXT,
            tunnel_type TEXT,
            data_sent_bytes INTEGER DEFAULT 0,
            data_received_bytes INTEGER DEFAULT 0,
            last_activity TEXT,
            entropy_score REAL DEFAULT 0.0,
            entropy_warning TEXT,
            data_type TEXT DEFAULT 'texto plano',
            implant_id INTEGER,
            FOREIGN KEY(implant_id) REFERENCES implants(id)
        );"""

@dataclass
class ImplantDB(BaseEntity):
    """
    Represents an implant payload persisted in the database.
    """
    id: int
    name: str
    implant_type: str
    payload: str
    description: str
    created_at: str
    supported_tunnel_type: str = None

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.name, self.implant_type, self.payload, self.description, self.created_at, self.supported_tunnel_type)

    @classmethod
    def insert(cls):
        return """INSERT INTO implants 
            (name, implant_type, payload, description, created_at, supported_tunnel_type) 
            VALUES (?, ?, ?, ?, ?, ?)"""

    @classmethod
    def update(cls):
        return """UPDATE implants SET 
            name=?, implant_type=?, payload=?, description=?, created_at=?, supported_tunnel_type=? 
            WHERE id=?"""

    @classmethod
    def delete(cls):
        return "DELETE FROM implants WHERE id=?"

    @classmethod
    def select(cls):
        return "SELECT id, name, implant_type, payload, description, created_at, supported_tunnel_type FROM implants;"

    @classmethod
    def selectById(cls):
        return "SELECT id, name, implant_type, payload, description, created_at, supported_tunnel_type FROM implants WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls, field):
        return f"SELECT id, name, implant_type, payload, description, created_at, supported_tunnel_type FROM implants WHERE {field} = ?;"

    @classmethod
    def create_table(cls):
        return """CREATE TABLE IF NOT EXISTS implants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            implant_type TEXT,
            payload TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now')),
            supported_tunnel_type TEXT
        );"""

class Templates(BaseEntity):
    def __init__(self, technique, name, desc, linux, windows, noise_estimate):
        self.technique = technique
        self.name = name
        self.desc = desc
        self.linux = linux
        self.windows = windows
        self.noise_estimate = noise_estimate

    @classmethod
    def create_table(cls):
        return """CREATE VIRTUAL TABLE IF NOT EXISTS templates_fts USING fts5(
            technique,
            name,
            desc,
            linux,
            windows,
            noise_estimate UNINDEXED
        );"""

    @classmethod
    def insert(cls):
        return """INSERT INTO templates_fts 
            (technique, name, desc, linux, windows, noise_estimate) 
            VALUES (?, ?, ?, ?, ?, ?)"""

    @classmethod
    def update(cls):
        return """UPDATE templates_fts 
            SET name=?, desc=?, linux=?, windows=?, noise_estimate=? 
            WHERE technique=?"""

    @classmethod
    def delete(cls):
        return """DELETE FROM templates_fts WHERE technique=?"""

    @classmethod
    def select(cls):
        return """SELECT technique, name, desc, linux, windows, noise_estimate FROM templates_fts"""

    @classmethod
    def selectById(cls):
        return """SELECT technique, name, desc, linux, windows, noise_estimate 
                  FROM templates_fts WHERE technique=?"""

    @classmethod
    def get_guid(cls) -> str:
        # El identificador único será la técnica MITRE (ej. T1021.002)
        return "technique"

    def exportAsTupple(self) -> tuple:
        return (self.technique, self.name, self.desc, self.linux, self.windows, self.noise_estimate)

    @classmethod
    def select_map(cls):
        return {
            "technique": 0,
            "name": 1,
            "desc": 2,
            "linux": 3,
            "windows": 4,
            "noise_estimate": 5
        }
    