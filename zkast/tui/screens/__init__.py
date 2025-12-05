"""TUI screens for zkast.

Screens are organized into categories:
- dashboard/ - Dashboard screens
- entry/ - Entry-related screens (create, edit, delete, list)
- tags/ - Tag-related screens (TODO)
- store/ - Store-related screens (TODO)
"""

from zkast.tui.screens.dashboard import MainScreen
from zkast.tui.screens.entry import EntryEditorScreen, EntryListScreen, EntryDeleteScreen

__all__ = [
    "MainScreen",
    "EntryEditorScreen",
    "EntryListScreen",
    "EntryDeleteScreen",
]
