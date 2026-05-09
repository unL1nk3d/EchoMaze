import sqlite3
import os
from queue import Queue
from GATHERINGDB.log import log

class SQLiteConnectionPool:
    _instance = None
    _DATABASE_PATH = None
    _DATABASE_POOL_SIZE = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLiteConnectionPool, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.validate_config()
        self.pool = Queue(maxsize=self._DATABASE_POOL_SIZE)
        for _ in range(self._DATABASE_POOL_SIZE):
            conn = sqlite3.connect(self._DATABASE_PATH, check_same_thread=False)
            self.pool.put(conn)
        self._initialized = True

    @classmethod
    def validate_config(cls):
        cls._DATABASE_PATH = os.environ.get("GATHERINGDB_DB_PATH", False)
        cls._DATABASE_POOL_SIZE = int(os.environ.get("GATHERINGDB_POOL_SIZE", 5))
        
        if not cls._DATABASE_PATH:
            raise ValueError("The environ variable GATHERINGDB_DB_PATH does not exist or it doesn't point to a db path directory")
        if not os.path.isfile(cls._DATABASE_PATH):
            log.warning(f"[!] CREATING A NEW DATABASE at {cls._DATABASE_PATH}!")

    def get_connection(self):
        return self.pool.get()

    def return_connection(self, conn):
        self.pool.put(conn)

    def close_all(self):
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
        self._initialized = False
        SQLiteConnectionPool._instance = None

    def __enter__(self):
        self._active_conn = self.get_connection()
        return self._active_conn

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, '_active_conn'):
            self.return_connection(self._active_conn)
            del self._active_conn

if __name__ == '__main__':
    # Usage
    os.environ["GATHERINGDB_DB_PATH"] = "test.db"
    pool = SQLiteConnectionPool()
    with pool as conn:
        print("Got connection")
    pool.close_all()
    if os.path.exists("test.db"):
        os.remove("test.db")
