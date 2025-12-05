"""SQLite storage implementation for zkast."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from zkast.storage.base import StorageInterface
from zkast.models.store import Store
from zkast.models.entry import Entry


class SQLiteStorage(StorageInterface):
    """SQLite implementation of storage interface."""

    def __init__(self, base_path: Path):
        """
        Initialize SQLite storage.

        Args:
            base_path: Base directory for storing databases
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._init_metadata_db()

    def _get_metadata_db_path(self) -> Path:
        """Get path to metadata database."""
        return self.base_path / "metadata.db"

    def _get_store_db_path(self, store_name: str) -> Path:
        """Get path to a store's database."""
        return self.base_path / f"{store_name}.db"

    def _init_metadata_db(self):
        """Initialize metadata database for tracking stores."""
        db_path = self._get_metadata_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                format TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def _init_store_db(self, store_name: str):
        """Initialize database for a specific store."""
        db_path = self._get_store_db_path(store_name)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        meta_conn = sqlite3.connect(str(self._get_metadata_db_path()))
        meta_cursor = meta_conn.cursor()
        meta_cursor.execute("SELECT id FROM stores WHERE name = ?", (store_name,))
        result = meta_cursor.fetchone()
        store_id = result[0] if result else None
        meta_conn.close()

        if not store_id:
            raise ValueError(f"Store {store_name} not found in metadata")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS entry_tags (
                entry_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (entry_id, tag_id),
                FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """
        )

        conn.commit()
        conn.close()

    def create_store(self, name: str, format: str = "sqlite") -> Store:
        """Create a new store."""
        if self.get_store(name):
            raise ValueError(f"Store '{name}' already exists")

        db_path = self._get_metadata_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO stores (name, format) VALUES (?, ?)",
            (name, format),
        )

        store_id = cursor.lastrowid
        cursor.execute(
            "SELECT name, format, created_at FROM stores WHERE id = ?",
            (store_id,),
        )
        row = cursor.fetchone()
        conn.commit()
        conn.close()

        self._init_store_db(name)

        return Store(
            id=store_id,
            name=row[0],
            format=row[1],
            created_at=datetime.fromisoformat(row[2]) if row[2] else None,
        )

    def list_stores(self) -> List[Store]:
        """List all available stores."""
        db_path = self._get_metadata_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, format, created_at FROM stores ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        stores = []
        for row in rows:
            stores.append(
                Store(
                    id=row[0],
                    name=row[1],
                    format=row[2],
                    created_at=datetime.fromisoformat(row[3]) if row[3] else None,
                )
            )

        return stores

    def get_store(self, name: str) -> Optional[Store]:
        """Get a store by name."""
        db_path = self._get_metadata_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, format, created_at FROM stores WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Store(
            id=row[0],
            name=row[1],
            format=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None,
        )

    def delete_store(self, name: str) -> bool:
        """Delete a store."""
        store = self.get_store(name)
        if not store:
            return False

        db_path = self._get_metadata_db_path()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stores WHERE name = ?", (name,))
        conn.commit()
        conn.close()

        store_db_path = self._get_store_db_path(name)
        if store_db_path.exists():
            store_db_path.unlink()

        return True

    def _get_store_id(self, store_name: str) -> int:
        """Get store ID by name."""
        store = self.get_store(store_name)
        if not store or not store.id:
            raise ValueError(f"Store '{store_name}' not found")
        return store.id

    def create_entry(self, store_name: str, entry: Entry) -> Entry:
        """Create a new entry in a store."""
        store_id = self._get_store_id(store_name)
        db_path = self._get_store_db_path(store_name)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO entries (store_id, message, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (store_id, entry.message, now, now),
        )

        entry_id = cursor.lastrowid

        tag_ids = []
        for tag_name in entry.tags:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid
            tag_ids.append(tag_id)

            cursor.execute(
                "INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
                (entry_id, tag_id),
            )

        conn.commit()

        cursor.execute(
            """
            SELECT id, message, created_at, updated_at
            FROM entries WHERE id = ?
        """,
            (entry_id,),
        )
        row = cursor.fetchone()

        cursor.execute(
            """
            SELECT t.name FROM tags t
            INNER JOIN entry_tags et ON t.id = et.tag_id
            WHERE et.entry_id = ?
        """,
            (entry_id,),
        )
        tag_rows = cursor.fetchall()
        tags = [row[0] for row in tag_rows]

        conn.close()

        return Entry(
            id=row[0],
            store_id=store_id,
            message=row[1],
            tags=tags,
            created_at=datetime.fromisoformat(row[2]) if row[2] else None,
            updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
        )

    def list_entries(self, store_name: str) -> List[Entry]:
        """List all entries in a store."""
        store_id = self._get_store_id(store_name)
        db_path = self._get_store_db_path(store_name)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, message, created_at, updated_at
            FROM entries WHERE store_id = ?
            ORDER BY created_at DESC
        """,
            (store_id,),
        )
        entry_rows = cursor.fetchall()

        entries = []
        for entry_row in entry_rows:
            entry_id = entry_row[0]

            cursor.execute(
                """
                SELECT t.name FROM tags t
                INNER JOIN entry_tags et ON t.id = et.tag_id
                WHERE et.entry_id = ?
            """,
                (entry_id,),
            )
            tag_rows = cursor.fetchall()
            tags = [row[0] for row in tag_rows]

            entries.append(
                Entry(
                    id=entry_id,
                    store_id=store_id,
                    message=entry_row[1],
                    tags=tags,
                    created_at=datetime.fromisoformat(entry_row[2]) if entry_row[2] else None,
                    updated_at=datetime.fromisoformat(entry_row[3]) if entry_row[3] else None,
                )
            )

        conn.close()
        return entries

    def update_entry(self, store_name: str, entry: Entry) -> Entry:
        """Update an existing entry in a store."""
        if not entry.id:
            raise ValueError("Entry ID is required for update")
        
        store_id = self._get_store_id(store_name)
        db_path = self._get_store_db_path(store_name)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if entry exists
        cursor.execute(
            "SELECT id FROM entries WHERE id = ? AND store_id = ?",
            (entry.id, store_id)
        )
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Entry with ID {entry.id} not found")

        # Update entry
        now = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE entries 
            SET message = ?, updated_at = ?
            WHERE id = ? AND store_id = ?
        """,
            (entry.message, now, entry.id, store_id),
        )

        # Remove old tags
        cursor.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry.id,))

        # Add new tags
        tag_ids = []
        for tag_name in entry.tags:
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid
            tag_ids.append(tag_id)

            cursor.execute(
                "INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
                (entry.id, tag_id),
            )

        conn.commit()

        # Fetch updated entry
        cursor.execute(
            """
            SELECT id, message, created_at, updated_at
            FROM entries WHERE id = ? AND store_id = ?
        """,
            (entry.id, store_id),
        )
        entry_row = cursor.fetchone()

        cursor.execute(
            """
            SELECT t.name FROM tags t
            INNER JOIN entry_tags et ON t.id = et.tag_id
            WHERE et.entry_id = ?
        """,
            (entry.id,),
        )
        tag_rows = cursor.fetchall()
        tags = [row[0] for row in tag_rows]

        updated_entry = Entry(
            id=entry_row[0],
            store_id=store_id,
            message=entry_row[1],
            tags=tags,
            created_at=datetime.fromisoformat(entry_row[2]) if entry_row[2] else None,
            updated_at=datetime.fromisoformat(entry_row[3]) if entry_row[3] else None,
        )

        conn.close()
        return updated_entry

    def delete_entry(self, store_name: str, entry_id: int) -> bool:
        """Delete an entry from a store."""
        store_id = self._get_store_id(store_name)
        db_path = self._get_store_db_path(store_name)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if entry exists
        cursor.execute(
            "SELECT id FROM entries WHERE id = ? AND store_id = ?",
            (entry_id, store_id)
        )
        if not cursor.fetchone():
            conn.close()
            return False

        # Delete entry tags first (foreign key constraint)
        cursor.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
        
        # Delete entry
        cursor.execute(
            "DELETE FROM entries WHERE id = ? AND store_id = ?",
            (entry_id, store_id)
        )

        conn.commit()
        conn.close()

        return cursor.rowcount > 0
