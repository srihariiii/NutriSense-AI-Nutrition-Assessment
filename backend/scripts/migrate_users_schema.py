import os
import shutil
import sqlite3

db_path = "data/nutrisense.db"
backend_db_path = "backend/data/nutrisense.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Inspect current users table
    cur.execute("PRAGMA table_info(users);")
    cols = [c[1] for c in cur.fetchall()]
    print("Old users table columns:", cols)

    if "first_name" not in cols:
        print("Migrating users table schema...")
        # Create temporary table with new schema
        cur.execute(
            """
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(100) NOT NULL DEFAULT '',
            last_name VARCHAR(100) NOT NULL DEFAULT '',
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        )

        # Copy existing data if any
        if "full_name" in cols and "password_hash" in cols:
            cur.execute(
                "SELECT id, full_name, email, password_hash, created_at FROM users;"
            )
            rows = cur.fetchall()
            for r in rows:
                user_id, full_name, email, pwd_hash, created_at = r
                parts = full_name.strip().split(" ", 1) if full_name else ["User", ""]
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
                cur.execute(
                    """
                INSERT INTO users_new (id, first_name, last_name, email, hashed_password, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                    (user_id, first_name, last_name, email, pwd_hash, created_at),
                )

        cur.execute("DROP TABLE users;")
        cur.execute("ALTER TABLE users_new RENAME TO users;")
        conn.commit()
        print("Successfully migrated users table!")

    cur.execute("PRAGMA table_info(users);")
    print("New users table columns:", [c[1] for c in cur.fetchall()])
    conn.close()

    os.makedirs("backend/data", exist_ok=True)
    shutil.copy(db_path, backend_db_path)
    print(f"Synced {db_path} -> {backend_db_path}")
