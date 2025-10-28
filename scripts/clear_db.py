import os
import sqlite3

# Resolve DB path relative to repo root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "exam.db")

TABLES_DELETE_ORDER = [
    # children first
    "answers",
    "proctor_images",
    "proctor_events",
    "attempts",
    "questions",
    "exams",
    "users",
]


def clear_database(db_path: str) -> None:
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Be friendly to concurrent processes; honor FKs; reduce lock contention
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA busy_timeout = 30000")

    # Merge any WAL pages to improve consistency before heavy ops
    try:
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass

    # Perform deletions in FK-safe order
    for table in TABLES_DELETE_ORDER:
        try:
            cur.execute(f"DELETE FROM {table}")
        except Exception as e:
            print(f"Warning: could not clear table '{table}': {e}")

    # Reset autoincrement counters if present
    try:
        cur.execute("DELETE FROM sqlite_sequence")
    except Exception:
        # sqlite_sequence may not exist depending on schema usage
        pass

    conn.commit()

    # Attempt to trim WAL and shrink DB file size
    try:
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass
    try:
        cur.execute("VACUUM")
    except Exception:
        pass

    conn.close()

    # Report row counts after clearing
    conn2 = sqlite3.connect(db_path, timeout=30)
    cur2 = conn2.cursor()
    print("Clear complete. Row counts:")
    for table in TABLES_DELETE_ORDER:
        try:
            cur2.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur2.fetchone()[0]
        except Exception as e:
            count = f"n/a ({e})"
        print(f"  {table}: {count}")
    conn2.close()


if __name__ == "__main__":
    print(f"Using database: {DB_PATH}")
    clear_database(DB_PATH)