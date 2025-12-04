"""Application state management for Zettelkasten."""
import json
from pathlib import Path
from typing import List, Optional

from zettelkasten.models.store import Store
from zettelkasten.models.entry import Entry
from zettelkasten.storage.base import StorageInterface


class AppState:
    """Singleton application state - single source of truth."""

    _instance: Optional["AppState"] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize application state."""
        if self._initialized:
            return

        self._current_store: Optional[Store] = None
        self._stores: List[Store] = []
        self._entries: List[Entry] = []
        self._storage: Optional[StorageInterface] = None
        self._base_path: Optional[Path] = None
        self._state_file: Optional[Path] = None
        self._initialized = True

    @property
    def current_store(self) -> Optional[Store]:
        """Get current active store."""
        return self._current_store

    @property
    def stores(self) -> List[Store]:
        """Get all stores."""
        return self._stores.copy()

    @property
    def entries(self) -> List[Entry]:
        """Get entries from current store."""
        return self._entries.copy()

    @property
    def storage(self) -> Optional[StorageInterface]:
        """Get storage interface."""
        return self._storage

    def initialize(self, base_path: Path, storage: StorageInterface):
        """
        Initialize state with base path and storage.

        Args:
            base_path: Base directory for zettelkasten
            storage: Storage interface implementation
        """
        self._base_path = Path(base_path)
        self._storage = storage
        self._state_file = self._base_path / ".state.json"
        self._load_state()

    def _load_state(self):
        """Load persisted state from file."""
        if not self._state_file or not self._state_file.exists():
            return

        try:
            with open(self._state_file, "r") as f:
                data = json.load(f)
                current_store_name = data.get("current_store")
                if current_store_name and self._storage:
                    self._current_store = self._storage.get_store(current_store_name)
        except (json.JSONDecodeError, IOError):
            # If state file is corrupted, ignore it
            pass

    def _save_state(self):
        """Save current state to file."""
        if not self._state_file:
            return

        try:
            data = {
                "current_store": self._current_store.name if self._current_store else None
            }
            with open(self._state_file, "w") as f:
                json.dump(data, f)
        except IOError:
            # If we can't save state, continue anyway
            pass

    def refresh_stores(self):
        """Refresh stores list from storage."""
        if not self._storage:
            return

        self._stores = self._storage.list_stores()

    def set_current_store(self, store: Store):
        """
        Set current active store and load its entries.

        Args:
            store: Store to set as current
        """
        self._current_store = store
        self._load_entries()
        self._save_state()

    def _load_entries(self):
        """Load entries from current store."""
        if not self._current_store or not self._storage:
            self._entries = []
            return

        try:
            self._entries = self._storage.list_entries(self._current_store.name)
        except Exception:
            self._entries = []

    def refresh_entries(self):
        """Refresh entries from current store."""
        self._load_entries()

    def add_entry(self, entry: Entry):
        """
        Add entry to current store.

        Args:
            entry: Entry to add
        """
        if not self._current_store or not self._storage:
            raise ValueError("No store selected")

        created_entry = self._storage.create_entry(self._current_store.name, entry)
        self._entries.insert(0, created_entry)  # Add to beginning
        return created_entry

