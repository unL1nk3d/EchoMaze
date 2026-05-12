from GATHERINGDB.dao import GenericDAO,Transaction#,log
from GATHERINGDB.model import (IPNode,Ports,Templates,WorkflowScoreConfig,
PivotHistory,Actions,Mitre_attack,Artifacts,Opsec_logs, TunnelDB, ImplantDB)
import sqlite3
import os
class DatabaseInitializer:
    ''' Clase para inicializar la base de datos '''
    @classmethod
    def initialize_db(cls,dao:GenericDAO=None):
        # crear la tabla si no existe
        models = [
            IPNode,Ports,Templates,WorkflowScoreConfig,
            PivotHistory,Actions,Mitre_attack,Artifacts,Opsec_logs, TunnelDB, ImplantDB
        ]
        with dao.conn() as connection:
            with Transaction(connection,dao.conn) as cursor:
                for x in models:
                    if not hasattr(x,'create_table'):
                        continue
                    cursor.execute(x.create_table())
    @classmethod
    def check_db_created(cls,core,dao):
        try:
            nodes = core.crud.show_all_data(IPNode,dao=dao)
        except sqlite3.OperationalError as e:
            #log.warning(msg="[*] Database or tables do not exist. Initializing database...")
            cls.initialize_db(dao)
            nodes = []