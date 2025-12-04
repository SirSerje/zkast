"""Abstract storage interface for Zettelkasten."""
from abc import ABC, abstractmethod
from typing import List, Optional

from zettelkasten.models.store import Store
from zettelkasten.models.entry import Entry


class StorageInterface(ABC):
    """Abstract interface for storage implementations using strategy pattern."""

    @abstractmethod
    def create_store(self, name: str, format: str = "sqlite") -> Store:
        """
        Create a new store.

        Args:
            name: Unique name for the store
            format: Storage format (default: sqlite)

        Returns:
            Created Store object

        Raises:
            ValueError: If store name already exists
        """
        pass

    @abstractmethod
    def list_stores(self) -> List[Store]:
        """
        List all available stores.

        Returns:
            List of Store objects
        """
        pass

    @abstractmethod
    def get_store(self, name: str) -> Optional[Store]:
        """
        Get a store by name.

        Args:
            name: Store name

        Returns:
            Store object if found, None otherwise
        """
        pass

    @abstractmethod
    def delete_store(self, name: str) -> bool:
        """
        Delete a store.

        Args:
            name: Store name to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def create_entry(self, store_name: str, entry: Entry) -> Entry:
        """
        Create a new entry in a store.

        Args:
            store_name: Name of the store
            entry: Entry object to create

        Returns:
            Created Entry with ID and timestamps set

        Raises:
            ValueError: If store doesn't exist
        """
        pass

    @abstractmethod
    def list_entries(self, store_name: str) -> List[Entry]:
        """
        List all entries in a store.

        Args:
            store_name: Name of the store

        Returns:
            List of Entry objects

        Raises:
            ValueError: If store doesn't exist
        """
        pass

