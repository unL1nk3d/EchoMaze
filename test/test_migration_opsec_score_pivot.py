import unittest
import sqlite3
from migrations.migration_001_add_opsec_score_pivot import upgrade, downgrade

class MigrationOpsecScorePivotTest(unittest.TestCase):
    def setUp(self):
        # In-memory DB with basic ip_node
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute("""
            CREATE TABLE ip_node (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                path TEXT NOT NULL,
                parent_ip TEXT,
                child_level INTEGER DEFAULT 0
            );
        """)
    def tearDown(self):
        self.conn.close()

    def test_upgrade(self):
        upgrade(self.conn)
        # Check new columns
        cur = self.conn.execute("PRAGMA table_info(ip_node)")
        cols = [r[1] for r in cur.fetchall()]
        self.assertIn('score', cols)
        self.assertIn('opsec_flag', cols)
        # Check new tables
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        self.assertIn('workflow_score_config', tables)
        self.assertIn('pivot_history', tables)

    def test_idempotent_upgrade(self):
        # Should not fail if run twice
        upgrade(self.conn)
        try:
            upgrade(self.conn)
        except Exception as e:
            self.fail(f"idempotent upgrade failed: {e}")

    def test_downgrade(self):
        upgrade(self.conn)
        downgrade(self.conn)
        # Columns should be gone
        cur = self.conn.execute("PRAGMA table_info(ip_node)")
        cols = [r[1] for r in cur.fetchall()]
        self.assertNotIn('score', cols)
        self.assertNotIn('opsec_flag', cols)
        # Tables should be dropped
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        self.assertNotIn('workflow_score_config', tables)
        self.assertNotIn('pivot_history', tables)

    def test_idempotent_downgrade(self):
        # Should not fail even if run twice
        upgrade(self.conn)
        downgrade(self.conn)
        try:
            downgrade(self.conn)
        except Exception as e:
            self.fail(f"idempotent downgrade failed: {e}")

    def test_upgrade_on_broken_table(self):
        # Remove 'ip_node' to simulate wrong schema
        self.conn.execute("DROP TABLE ip_node;")
        with self.assertRaises(Exception):
            upgrade(self.conn)  # Should fail meaningfully

if __name__ == '__main__':
    unittest.main()
