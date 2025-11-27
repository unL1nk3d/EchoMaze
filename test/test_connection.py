import unittest
from unittest.mock import patch, MagicMock
from queue import Queue
import sqlite3
import os

# Ajusta el import según tu estructura
from GATHERINGDB.connection import SQLiteConnectionPool

class TestSQLiteConnectionPool(unittest.TestCase):
    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "/tmp/test.db",
        "GATHERINGDB_POOL_SIZE": "3"
    })
    @patch("os.path.isfile", return_value=True)
    @patch("sqlite3.connect")
    def test_pool_initialization(self, mock_connect, mock_isfile):
        pool = SQLiteConnectionPool()
        self.assertEqual(pool.pool.qsize(), 3)
        mock_connect.assert_called_with("/tmp/test.db", check_same_thread=False)

    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "/tmp/test.db",
        "GATHERINGDB_POOL_SIZE": "2"
    })
    @patch("os.path.isfile", return_value=True)
    @patch("sqlite3.connect")
    def test_get_and_return_connection(self, mock_connect, mock_isfile):
        pool = SQLiteConnectionPool()
        conn = pool.get_connection()
        self.assertIsNotNone(conn)
        pool.return_connection(conn)
        self.assertEqual(pool.pool.qsize(), 2)

    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "/tmp/test.db",
        "GATHERINGDB_POOL_SIZE": "2"
    })
    @patch("os.path.isfile", return_value=True)
    @patch("sqlite3.connect")
    def test_close_all_connections(self, mock_connect, mock_isfile):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pool = SQLiteConnectionPool()
        pool.close_all()
        self.assertEqual(pool.pool.qsize(), 0)
        self.assertEqual(mock_conn.close.call_count, 2)

    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "/tmp/test.db",
        "GATHERINGDB_POOL_SIZE": "1"
    })
    @patch("os.path.isfile", return_value=True)
    @patch("sqlite3.connect")
    def test_context_manager(self, mock_connect, mock_isfile):
        pool = SQLiteConnectionPool()
        with patch.object(pool, 'return_connection') as mock_return:
            with pool as conn:
                self.assertIsNotNone(conn)
            mock_return.assert_called_once()

    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "",
        "GATHERINGDB_POOL_SIZE": "2"
    })
    def test_validate_path_missing_env(self):
        with self.assertRaises(ValueError):
            SQLiteConnectionPool.validate_path()

    @patch.dict(os.environ, {
        "GATHERINGDB_DB_PATH": "/tmp/test.db",
        "GATHERINGDB_POOL_SIZE": "2"
    })
    @patch("os.path.isfile", return_value=False)
    def test_validate_path_creates_db_warning(self, mock_isfile):
        with patch("GATHERINGDB.log.log.warning") as mock_log:
            SQLiteConnectionPool.validate_path()
            mock_log.assert_called_with("[!] CREATING A NEW DATABASE!")

if __name__ == '__main__':
    unittest.main()
