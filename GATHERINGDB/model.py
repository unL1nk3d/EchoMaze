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
        # returns an attribute that is the unique identifier of the class
        raise NotImplementedError("Subclasses must implement get_guid method")
    def exportAsTupple(self) -> tuple:
        # returns the attributes of the class as a tupple
        raise NotImplementedError("Subclasses must implement exportAsTupple method")
    @classmethod
    def create_table() -> str:
        # returns the SQL statement to create the table
        raise NotImplementedError("Subclasses must implement create_table method")
    @classmethod
    def select(cls) -> str:
        # returns the SQL statement to select all records from the table
        raise NotImplementedError("Subclasses must implement select method")
    @classmethod
    def selectById(cls) -> str:
        # returns the SQL statement to select a record by its unique identifier
        raise NotImplementedError("Subclasses must implement selectById method")
    @classmethod
    def selectCoincidence(cls) -> str:
        # returns the SQL statement to select records by a field and value
        raise NotImplementedError("Subclasses must implement selectCoincidence method")
@dataclass
class IPNode(BaseEntity):
    id: int
    ip: str
    path:str
    parent_ip: str = None
    child_level:int = 0
    @classmethod
    def get_guid():
        return 'ip'
    @classmethod
    def insert(cls):
        return f"INSERT INTO ip_node(ip,path,parent_ip,child_level) VALUES (?,?,?,?)"
    @classmethod
    def update(cls):
        return f"UPDATE ip_node SET ip=?, path=?, parent_ip=? WHERE ip=?"
    @classmethod
    def delete(cls):
        return f"DELETE FROM ip_node WHERE id=?"
    def exportAsTupple(self):
        return (self.ip,self.path,self.parent_ip,self.child_level)
    @classmethod
    def select(cls):
        
        return "SELECT id, ip, path, parent_ip,child_level FROM ip_node"
    @classmethod
    def selectById(cls):
        return "SELECT id, ip, path, parent_ip FROM ip_node WHERE id=?"
    @classmethod
    def select_map(cls):
        sm = {
            "ip":"SELECT id, ip, path, parent_ip FROM ip_node WHERE  ip = ?",
            "id":"SELECT id, ip, path, parent_ip FROM ip_node WHERE  id = ?",
            "parent_ip":"SELECT id, ip, path, parent_ip FROM ip_node WHERE  parent_ip = ?",
            "child_level":"SELECT id, ip, path, parent_ip FROM ip_node WHERE  child_level = ?",
            "max_child_level_by_parent":"SELECT MAX(child_level) as max_level FROM ip_node where parent_ip = ?"
        }
        return sm
    @classmethod
    def selectCoincidence(cls,field):
        # select map realmente solo son consultas especificas por campo para evitar tener que 
        # crear una consulta que se altere en tiempo de ejecucion que es riesgoso
        sm = cls.select_map().get(field,None)
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
                child_level INTEGER DEFAULT 0
            )
        '''
    
        
@dataclass
class Ports(BaseEntity):
    id: int
    port:int
    service_name:str
    ip:str
    @classmethod
    def get_guid():
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
            "ip":"SELECT id, port, service_name,ip parent_ip FROM ports WHERE  ip = ?",
            "id":"SELECT id, port, service_name,ip FROM ports WHERE  id = ?"
        }
        return sm
    @classmethod
    def selectCoincidence(cls,field):
        # select map realmente solo son consultas especificas por campo para evitar tener que 
        # crear una consulta que se altere en tiempo de ejecucion que es riesgoso
        sm = cls.select_map().get(field,None)
        if not sm:
            raise ValueError(f"No se definio una consulta de tipo {field} en {cls.__name__} ")
        return sm
    def exportAsTupple(self):
        return (self.port,self.service_name,self.ip)    
    def create_table():
        return '''
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                ip TEXT NOT NULL,
                FOREIGN KEY(ip) REFERENCES ip_node(ip)
            )
        '''



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
        return (self.id, self.node_id, self.action_type, self.command_template, self.parameters,
                self.mitre_ttp_id, self.timestamp, self.operator, self.noise_score)

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
    def selectCoincidence(cls):
        return "SELECT * FROM actions WHERE {} = ?;"
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
    def selectCoincidence(cls):
        return "SELECT * FROM mitre_attack WHERE {} = ?;"

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

    @classmethod
    def get_guid(cls):
        return "id"

    def exportAsTupple(self):
        return (self.id, self.filename, self.node_id, self.sha1, self.sha256, self.md5,
                self.size, self.created_at, self.notes)

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
            FOREIGN KEY(node_id) REFERENCES nodes(id)
        );"""

    @classmethod
    def select(cls):
        return "SELECT * FROM artifacts;"

    @classmethod
    def selectById(cls):
        return "SELECT * FROM artifacts WHERE id = ?;"

    @classmethod
    def selectCoincidence(cls):
        return "SELECT * FROM artifacts WHERE {} = ?;"

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
        return (self.id, self.action_id, self.event, self.severity, self.details, self.created_at)

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
    def selectCoincidence(cls):
        return "SELECT * FROM opsec_logs WHERE {} = ?;"



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