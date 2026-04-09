"""
Migration: Add score and opsec_flag to ip_node, workflow_score_config and pivot_history tables.
Usage:
    from migration_001_add_opsec_score_pivot import upgrade, downgrade
    upgrade(conn)
    downgrade(conn)
"""

import sqlite3

def upgrade(conn):
    """
    Apply the migration: Add 'score' and 'opsec_flag' fields to 'ip_node',
    and create 'workflow_score_config' and 'pivot_history' tables.
    """
    cursor = conn.cursor()
    # Add columns only if they don't exist
    for col, col_type in [("score", "INTEGER DEFAULT 0"), ("opsec_flag", "INTEGER DEFAULT 0")]:
        cursor.execute("PRAGMA table_info(ip_node);")
        columns = [row[1] for row in cursor.fetchall()]
        if col not in columns:
            cursor.execute(f"ALTER TABLE ip_node ADD COLUMN {col} {col_type};")
    # Create workflow_score_config table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflow_score_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL
    );
    """)
    # Create pivot_history table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pivot_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        user TEXT,
        event TEXT NOT NULL,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

def downgrade(conn):
    """
    Downgrade the migration: Remove 'score' and 'opsec_flag' from 'ip_node',
    and drop 'workflow_score_config' and 'pivot_history' tables.
    WARNING: Column remove in SQLite needs table recreation!
    """
    cursor = conn.cursor()
    # Drop workflow_score_config and pivot_history
    cursor.execute("DROP TABLE IF EXISTS workflow_score_config;")
    cursor.execute("DROP TABLE IF EXISTS pivot_history;")
    # Remove columns from ip_node: need to recreate table
    cursor.execute("PRAGMA table_info(ip_node);")
    columns = [row[1] for row in cursor.fetchall()]
    cols_to_keep = [c for c in columns if c not in ('score', 'opsec_flag')]
    if len(cols_to_keep) != len(columns):  # Only if columns to drop exist
        cols_str = ", ".join(cols_to_keep)
        cursor.execute(f"ALTER TABLE ip_node RENAME TO ip_node_old;")
        # Get original column definitions (minimal!)
        cursor.execute(f"CREATE TABLE ip_node AS SELECT {cols_str} FROM ip_node_old;")
        cursor.execute(f"DROP TABLE ip_node_old;")
    conn.commit()