"""
CampusConnect SQLite Database Inspector CLI
Use this script to view all tables and rows in .db/campusconnect.db from the terminal!
"""
import os
import sys
import sqlite3

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".db", "campusconnect.db")

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at: {DB_PATH}")
        print("Run 'python init_db.py' or 'python server.py' to generate it.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 70)
    print(f"  CampusConnect SQLite Database Viewer")
    print(f"  File: {DB_PATH}")
    print("=" * 70)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\n--- Table: {table} ({count} rows) ---")

        cursor.execute(f"SELECT * FROM {table} LIMIT 10;")
        rows = cursor.fetchall()
        if not rows:
            print("  (Empty table)")
            continue

        # Print header
        col_names = rows[0].keys()
        print("  | " + " | ".join(col_names) + " |")
        print("  |-" + "-|-".join(["-" * len(c) for c in col_names]) + "-|")

        for row in rows:
            vals = [str(row[c]) if row[c] is not None else "NULL" for c in col_names]
            # Truncate long strings for terminal
            vals = [v[:25] + "..." if len(v) > 25 else v for v in vals]
            print("  | " + " | ".join(vals) + " |")

    conn.close()
    print("\n" + "=" * 70)
    print("  You can also open this file directly in 'DB Browser for SQLite':")
    print(f"  --> {DB_PATH}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    inspect_db()
