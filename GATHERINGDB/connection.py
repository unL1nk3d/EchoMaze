import sqlite3
from sys import exit
from GATHERINGDB.log import log
import sqlite3
import os
from queue import Queue

class SQLiteConnectionPool:
    _DATABASE_PATH = os.environ.get("GATHERINGDB_DB_PATH",False)
    _DATABASE_POOL_SIZE = os.environ.get("GATHERINGDB_POOL_SIZE",5)
    def __init__(self):
        self.validate_path()
        self.pool = Queue(maxsize=SQLiteConnectionPool._DATABASE_POOL_SIZE)
        for _ in range(SQLiteConnectionPool._DATABASE_POOL_SIZE):
            conn = sqlite3.connect(SQLiteConnectionPool._DATABASE_PATH, check_same_thread=False)
            self.pool.put(conn)

    def get_connection(self):
        return self.pool.get()

    def return_connection(self, conn):
        self.pool.put(conn)

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
    def __enter__(self):
        return self.get_connection()
    def __exit__(self, exc_type, exc_value, traceback):
        log.warning("Exiting context manager, returning connection to pool", exc_info=(exc_type, exc_value, traceback))
        self.return_connection(self)
        

    @classmethod
    def validate_path(cls):
        if not(cls._DATABASE_PATH):
            raise ValueError("The environ vareable GATHERINGDB_DB_PATH donot exists or it dont point to a db path directory")
        if not(os.path.isfile(cls._DATABASE_PATH)):
            log.warning("[!] CREATING A NEW DATABASE!")
        if isinstance(cls._DATABASE_POOL_SIZE,str):
            cls._DATABASE_POOL_SIZE = int(cls._DATABASE_POOL_SIZE)
    ...
if __name__ == '__main__':
    # Usage
    pool = SQLiteConnectionPool()
    conn = pool.get_connection()
    # Use the connection...
    pool.return_connection(conn)
    pool.close_all()