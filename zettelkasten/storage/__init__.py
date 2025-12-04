"""Storage layer for Zettelkasten."""
from zettelkasten.storage.base import StorageInterface
from zettelkasten.storage.sqlite_storage import SQLiteStorage

__all__ = ["StorageInterface", "SQLiteStorage"]

