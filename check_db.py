"""
Aetheris Omni-Agent: SQLite Database Inspector Utility
Run anytime with: python check_db.py
"""

import sqlite3
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "mcp_server", "concierge_data.db")

def inspect_database():
    if not os.path.exists(DB_PATH):
        print(f"[-] Database file not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("[*] AETHERIS SQLITE DATABASE INSPECTOR")
    print(f"[*] File Location: {DB_PATH}")
    print("="*70)

    # 1. List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row["name"] for row in cursor.fetchall()]
    print(f"\n[*] Connected Tables ({len(tables)}): {', '.join(tables)}\n")

    # 2. Inspect each table contents
    for table in tables:
        print("-" * 70)
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        print(f"[*] Table: [{table.upper()}] (Total Rows: {len(rows)})")
        
        if rows:
            # Print column headers
            columns = rows[0].keys()
            print("   Columns: " + " | ".join(columns))
            # Print up to 3 sample rows
            for r in rows[:3]:
                vals = [str(r[c])[:25] for c in columns]
                print("   → " + " | ".join(vals))
            if len(rows) > 3:
                print(f"   ... and {len(rows) - 3} more rows")
        else:
            print("   (Empty table)")
        print()

    conn.close()
    print("="*70 + "\n")

if __name__ == "__main__":
    inspect_database()
