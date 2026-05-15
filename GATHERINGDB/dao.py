import sqlite3
from GATHERINGDB.model import IPNode, IntegrityError, WorkflowScoreConfig, PivotHistory
from GATHERINGDB.connection import SQLiteConnectionPool
from GATHERINGDB.log import log
from GATHERINGDB.model import BaseEntity
from typing import TypeVar, Generic, List

T = TypeVar('T')  # T puede ser cualquier tipo

class Transaction:
    def __init__(self, connection: SQLiteConnectionPool, poolToAsk: SQLiteConnectionPool):
        self.connection = connection
        self.poolToAsk = poolToAsk()
        self.is_acquired_connection = False
        self.cursor = None

    def __enter__(self):
        if self.connection is None:
            self.connection = self.poolToAsk.get_connection()
            self.is_acquired_connection = True
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
            log.error("Transaction failed, rolling back.", exc_info=(exc_type, exc_value, traceback))
        self.cursor.close()
        if self.is_acquired_connection:
            self.poolToAsk.return_connection(self.connection)

class GenericDAO:
    conn = SQLiteConnectionPool
    # ... (resto igual)

    # Métodos CRUD genericos (sin cambios)
    @classmethod
    def createTable(cls, entity_class):
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                cursor.execute(entity_class.create_table())

    # Reutiliza todos los métodos (insertar, actualizar...) idénticos para cualquier BaseEntity

    @classmethod
    def seleccionar(cls, data: BaseEntity, top_results: int = None) -> List[T]:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                cursor.execute(data.select())
                if top_results:
                    regis = [data(*reg) if reg else None for reg in cursor.fetchmany(top_results)]
                else:
                    regis = [data(*reg) if reg else None for reg in cursor.fetchall()]
                return regis

    @classmethod
    def seleccionarPorId(cls, data: T, id: int) -> T:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                valores = (id,)
                query = getattr(data, 'selectById', None)
                sql = query()
                if not callable(query):
                    raise ValueError(f"El modelo {data} no tiene un método selectById()")
                cursor.execute(sql, valores)
                reg = cursor.fetchone()
                if not reg:
                    return None
                return data(*reg)

    @classmethod
    def insertar(cls, data: T) -> int:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                valores = data.exportAsTupple()
                query = getattr(data, 'insert', None)
                if not callable(query):
                    raise ValueError(f"El modelo {data} no tiene un método insert()")
                sql = query()
                try:
                    cursor.execute(sql, valores)
                except sqlite3.IntegrityError as e:
                    log.error(f"Error de integridad al insertar {data}: {e}")
                    raise IntegrityError(type(data).__name__) from e
                return cursor.lastrowid
        return 0

    @classmethod
    def actualizar(cls, data: T, id: int) -> int:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                values = [x for x in data.exportAsTupple()]
                values.append(id)  # id as last element
                query = getattr(data, 'update', None)
                sql = query()
                if not callable(query):
                    raise ValueError(f"El modelo {data} no tiene un método update()")
                cursor.execute(sql, values)
                count = cursor.rowcount
        return count

    @classmethod
    def eliminar(cls, data: T, id: int) -> int:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                valores = (id,)
                sql = getattr(data, 'delete', None)
                sql = sql()
                if not sql:
                    raise ValueError(f"El modelo {data} no tiene un método delete()")
                cursor.execute(sql, valores)
                log.warn(f"Eliminando registro con id {id} usando {sql} y valores {valores}")
                rs = cursor.rowcount
        return rs

    @classmethod
    def seleccionarCoincidencia(cls, data: T, field: str, value: str) -> List[T]:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                sql = getattr(data, 'selectCoincidence', None)
                sql = sql(field)
                if not sql:
                    raise ValueError(f"El modelo {data} no tiene un método selectCoincidence()")
                valores = (value,)
                cursor.execute(sql, valores)
                regis = [data(*reg) if reg else None for reg in cursor.fetchall()]
                return regis

    @classmethod
    def seleccionarCoincidenciaFTS(cls, data: T, text: str) -> list:
        with cls.conn() as connection:
            with Transaction(connection, cls.conn) as cursor:
                sql = f"SELECT * FROM templates_fts WHERE templates_fts MATCH ?"
                cursor.execute(sql, (text,))
                return cursor.fetchall()

# -- Métodos CRUD explícitos para las nuevas entidades, por claridad y edge-cases (opcional, el abstracción anterior ya los cubre).
# Se documentan sólo como ejemplo:

def test_workflow_score_config_crud():
    entry = WorkflowScoreConfig(id=None, name="stealth", value=4.5, description="Stealth test config")
    res_insert = GenericDAO.insertar(entry)
    # ... resto igual que los métodos base ...

def test_pivot_history_crud():
    entry = PivotHistory(id=None, source_ip="10.0.0.1", dest_ip="10.0.0.2", operator="alice", timestamp="2023-01-01T12:00:00", details="pivot test")
    res_insert = GenericDAO.insertar(entry)
    # ... resto igual ...

# La arquitectura base no requiere modificaciones más allá de los data model
# Los métodos genéricos ya cubren todas las entidades tipo BaseEntity
