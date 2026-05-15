"""
Migration: Add data_type field to tunnels table.
Usage:
    from migration_002_add_tunnel_data_type import upgrade, downgrade
    upgrade(conn)
    downgrade(conn)
"""

import sqlite3

def upgrade(conn):
    """
    Apply the migration: Add 'data_type' field to 'tunnels'.
    """
    cursor = conn.cursor()
    # Add column only if it doesn't exist
    col = "data_type"
    col_type = "TEXT DEFAULT 'texto plano'"
    
    cursor.execute("PRAGMA table_info(tunnels);")
    columns = [row[1] for row in cursor.fetchall()]
    if col not in columns:
        cursor.execute(f"ALTER TABLE tunnels ADD COLUMN {col} {col_type};")
    
    conn.commit()

def downgrade(conn):
    """
    Downgrade the migration: Remove 'data_type' from 'tunnels'.
    WARNING: Column remove in SQLite needs table recreation!
    """
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(tunnels);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'data_type' in columns:
        cols_to_keep = [c for c in columns if c != 'data_type']
        cols_str = ", ".join(cols_to_keep)
        cursor.execute(f"ALTER TABLE tunnels RENAME TO tunnels_old;")
        # Recreate table using the new schema (which doesn't have data_type)
        # Note: For a real migration system, we'd use the create_table SQL from the previous version.
        # Here we just select into a new table.
        cursor.execute(f"CREATE TABLE tunnels AS SELECT {cols_str} FROM tunnels_old;")
        cursor.execute(f"DROP TABLE tunnels_old;")
        
    conn.commit()
