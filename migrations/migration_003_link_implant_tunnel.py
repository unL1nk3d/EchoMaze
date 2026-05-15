"""
Migration: Link Implants and Tunnels.
- Add supported_tunnel_type to implants table.
- Add implant_id to tunnels table.
"""

import sqlite3

def upgrade(conn):
    cursor = conn.cursor()
    
    # Update implants table
    cursor.execute("PRAGMA table_info(implants);")
    implant_cols = [row[1] for row in cursor.fetchall()]
    if "supported_tunnel_type" not in implant_cols:
        cursor.execute("ALTER TABLE implants ADD COLUMN supported_tunnel_type TEXT;")
        
    # Update tunnels table
    cursor.execute("PRAGMA table_info(tunnels);")
    tunnel_cols = [row[1] for row in cursor.fetchall()]
    if "implant_id" not in tunnel_cols:
        cursor.execute("ALTER TABLE tunnels ADD COLUMN implant_id INTEGER;")
        
    conn.commit()

def downgrade(conn):
    # Standard SQLite downgrade (recreate tables) is skipped for brevity in this task 
    # unless explicitly requested, but usually involves RENAME -> CREATE -> INSERT -> DROP.
    pass
