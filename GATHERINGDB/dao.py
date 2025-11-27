import sqlite3
from GATHERINGDB.model import IPNode,IntegrityError 
from GATHERINGDB.connection import SQLiteConnectionPool
from GATHERINGDB.log import log
from GATHERINGDB.model import BaseEntity,IPNode
from typing import TypeVar, Generic, List

T = TypeVar('T')  # T puede ser cualquier tipo


class Transaction:
    def __init__(self, connection: SQLiteConnectionPool,poolToAsk:SQLiteConnectionPool):
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
            self.connection.return_connection(self.connection)        
        
class GenericDAO:
    ''' 
    contiene los quertys para ejecutar las acciones 
    realizara las operaciones sobre la base de datos de
    persona
    DA0 -> DATA ACCESS OBJECT
    
    LA CLASE PERSONA ES UNA CLASE DE ENTIDAD QUE ALMACENARA
    LOS REGISTROS DE LA BASE DE DATOS
    
    LA CLASE DAO CONTIENE LOS METODOS PAR ALEER ACTUALIZAR O INSERTAR DATOS
    DAO ES UN PATRON DE DISE;O
    
    CRUD
    
    C -> CREADE
    R -> READ
    U -> UPDATE
    D -> DELETE
    '''
    # conn almacena la clase/constructor del pool; instanciar con cls.conn()
    conn = SQLiteConnectionPool
    #_SELECCIONAR = 'SELECT * FROM persona ORDER BY id_persona;'
    #_INSERTAR = 'INSERT INTO persona(nombre,apellido,email) values (%s,%s,%s);'
    #_ACTUALIZAR = 'UPDATE persona SET nombre=%s,apellido=%s,email=%s WHERE id_persona=%s;'
    #_ELIMINAR = 'DELETE FROM persona WHERE id_persona=%s;'
    @classmethod
    def createTable(cls):
        ...
    
    @classmethod
    def seleccionar(cls,data:BaseEntity,top_results:int = None) -> list[T]:
        # permite pasar una transacción opcional en el futuro; por ahora abrimos
        # una transacción temporal para lectura
        with cls.conn() as connection:
            with Transaction(connection,cls.conn) as cursor:
                cursor.execute(data.select()) 
                if top_results:
                    regis = [ data(*reg) if reg else None for reg in cursor.fetchmany(top_results)]
                else:
                    regis = [ data(*reg) if reg else None for reg in cursor.fetchall()]
                return regis  
    @classmethod
    def seleccionarPorId(cls,data:T,id:int) -> T:
        with cls.conn() as conection:
            with Transaction(conection,cls.conn) as cursor:
                valores = (id,)
                query = getattr(data,'selectById',None)
                sql = query()
                if not(callable(query)):
                    raise ValueError(f"El modelo {data} no tiene un método selectById()")
                cursor.execute(sql,valores)
                reg = cursor.fetchone()
                if not reg:
                    return None
                return data(*reg)

    @classmethod
    def insertar(cls,data:T) -> int:
        ''' se necesita una transaccion por lo que usamos un width conexion '''
        with cls.conn() as connection:
            with Transaction(connection,cls.conn) as cursor:
                valores = data.exportAsTupple()
                # el modelo define insert() como método que devuelve la query
                query = getattr(data, 'insert', None)
                if not(callable(query)):
                    raise ValueError(f"El modelo {data} no tiene un método insert()")
                sql = query()
                try:
                    cursor.execute(sql, valores)
                except sqlite3.IntegrityError as e:
                    log.error(f"Error de integridad al insertar {data}: {e}")
                    raise IntegrityError(type(data).__name__) from e
                cmps = cursor.rowcount
        return cmps
    @classmethod
    def actualizar(cls,data:T,id:int) -> int:
        ''' retorna las filas afectadas '''
        # hacemos una transaccion por lo tanto debemos de abrir la conexion con width
        with cls.conn() as connection:
            with Transaction(connection,cls.conn) as cursor:
                values = [x for x in data.exportAsTupple()]
                values.append(id)# id should be appened at the end
                # el modelo define update() que devuelve la query
                query = getattr(data, 'update', None)
                sql = query()
                if not callable(query):
                    raise ValueError(f"El modelo {data} no tiene un método update()")
                cursor.execute(sql, values)
                count = cursor.rowcount
        return count
    @classmethod
    def eliminar(cls,data:T,id:int) -> int:
        with cls.conn() as connection:
            with Transaction(connection,cls.conn) as cursor:
                valores = (id,)
                # usar la query de la clase si existe
                sql = getattr(data, 'delete', None)
                sql = sql()
                if not sql:
                    # intentar usar una función delete en el modelo
                    raise ValueError(f"El modelo {data} no tiene un método delete()")
                cursor.execute(sql, valores)
                log.warn(f"Eliminando registro con id {id} usando {sql} y valores {valores}")
                rs = cursor.rowcount
        return rs
    @classmethod
    def seleccionarCoincidencia(cls,data:T,field:str,value:str) -> list[T]:
        with cls.conn() as connection:
            with Transaction(connection,cls.conn) as cursor:
                sql = getattr(data, 'selectCoincidence', None)
                sql = sql(field)
                if not sql:
                    raise ValueError(f"El modelo {data} no tiene un método selectCoincidence()")
                valores = (value,)
                cursor.execute(sql,valores)
                regis = [ data(*reg) if reg else None for reg in cursor.fetchall()]
                return regis