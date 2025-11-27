import os

# Lista de nombres de directorios
work_dirs = ['context', 'exploits', 'scan']

def make_dirs():
    # Crear cada directorio si no existe
    for dir_name in work_dirs:
        os.makedirs(dir_name, exist_ok=True)

# AUTOMATIC DB GATHERING (GATHERINGDB)

from dataclasses import dataclass

@dataclass
class IPNode:
    ip: str
    path:str
    parent_ip: str = None
    child_level: int = 0

import sqlite3
from model import IPNode

class IPNodeDAO:
    def __init__(self, db_path='ip_tree.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_node (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                path TEXT NOT NULL,
                parent_ip TEXT,
                child_level INTEGER DEFAULT 0
            )
        ''')

    def insert_node(self, node: IPNode):
        self.cursor.execute(
            'INSERT INTO ip_nodes (ip, path,parent_ip,child_level) VALUES (?, ? ,?,?)',
            (node.ip, node.path,node.parent_ip,node.child_level)
        )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

import os
from dao import IPNodeDAO
from model import IPNode

BASE_DIR = 'lab'

def insert_ip_tree(current_path, parent_ip=None, dao=None):
    for entry in os.listdir(current_path):
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            node = IPNode(ip=entry, parent_ip=parent_ip,path=full_path)
            dao.insert_node(node)
            insert_ip_tree(full_path, entry, dao)

def main():
    dao = IPNodeDAO()
    insert_ip_tree(BASE_DIR, dao=dao)
    dao.commit()
    dao.close()

if __name__ == '__main__':
    main()

    """
ip_tree_project/
├── dao.py           # Acceso a la base de datos
├── model.py         # Definición de entidades
├── main.py          # Lógica principal y recorrido de directorios

    """