"""Controls layer for user interactions and future API."""

from typing import Optional, Callable, Any, List
from pathlib import Path

from zkast.state import AppState
from zkast.storage.base import StorageInterface
from zkast.models.store import Store
from zkast.models.entry import Entry


class Controls:
    """
    Controls layer - handles user interactions and orchestrates state/storage.

    This layer acts as the intermediary between user input (keyboard, future API)
    and the application state/storage layers.
    """

    def __init__(self, state: AppState, storage: StorageInterface):
        """
        Initialize controls layer.

        Args:
            state: Application state instance
            storage: Storage interface implementation
        """
        self.state = state
        self.storage = storage

    def create_store(self, name: str, format: str = "sqlite") -> Store:
        """
        Create a new store.

        Args:
            name: Store name
            format: Storage format

        Returns:
            Created store

        Raises:
            ValueError: If store creation fails
        """
        store = self.storage.create_store(name, format)
        self.state.refresh_stores()
        return store

    def list_stores(self) -> List[Store]:
        """
        List all stores.

        Returns:
            List of stores
        """
        self.state.refresh_stores()
        return self.state.stores

    def switch_store(self, name: str) -> bool:
        """
        Switch to a different store.

        Args:
            name: Store name to switch to

        Returns:
            True if switched successfully, False otherwise
        """
        store = self.storage.get_store(name)
        if not store:
            return False

        self.state.set_current_store(store)
        return True

    def delete_store(self, name: str) -> bool:
        """
        Delete a store.

        Args:
            name: Store name to delete

        Returns:
            True if deleted, False otherwise
        """
        if self.state.current_store and self.state.current_store.name == name:
            return False

        success = self.storage.delete_store(name)
        if success:
            self.state.refresh_stores()
        return success

    def create_entry(self, message: str, tags: List[str]) -> Entry:
        """
        Create a new entry in the current store.

        Args:
            message: Entry message content
            tags: List of tags

        Returns:
            Created entry

        Raises:
            ValueError: If no store is selected
        """
        if not self.state.current_store:
            raise ValueError("No store selected")

        entry = Entry(message=message, tags=tags)
        return self.state.add_entry(entry)

    def list_entries(self) -> List[Entry]:
        """
        List all entries in the current store.

        Returns:
            List of entries

        Raises:
            ValueError: If no store is selected
        """
        if not self.state.current_store:
            raise ValueError("No store selected")

        self.state.refresh_entries()
        return self.state.entries
