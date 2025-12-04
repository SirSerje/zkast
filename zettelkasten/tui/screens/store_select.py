"""Store selection screen for Zettelkasten TUI."""
from typing import Optional
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Select
from textual.binding import Binding

from zettelkasten.state import AppState


class StoreSelectScreen(ModalScreen):
    """Screen for selecting, switching, and deleting stores."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("n", "new_store", "New Store"),
    ]

    def __init__(self):
        """Initialize store select screen."""
        super().__init__()
        self.state = AppState()
        self._selected_store: Optional[str] = None

    def compose(self):
        """Compose the screen."""
        yield Container(
            Vertical(
                Static("Store Management", id="title"),
                Static("", id="status"),
                Static("Select a store:", id="select-label"),
                Select([], id="store-select", prompt="Choose a store..."),
                Horizontal(
                    Button("Switch", id="switch-btn", variant="primary"),
                    Button("Delete", id="delete-btn", variant="error"),
                    Button("New Store", id="new-btn"),
                    Button("Cancel", id="cancel-btn"),
                ),
                id="store-select-container",
            )
        )

    def on_mount(self):
        """Called when screen is mounted."""
        self.refresh_stores()

    def refresh_stores(self):
        """Refresh the store list."""
        self.state.refresh_stores()
        store_select = self.query_one("#store-select", Select)
        
        # Build options list
        options = []
        for store in self.state.stores:
            is_current = (
                self.state.current_store
                and self.state.current_store.name == store.name
            )
            label = f"{'* ' if is_current else ''}{store.name} ({store.format})"
            options.append((label, store.name))
        
        # Update Select widget
        store_select.set_options(options)
        
        # Set current selection if there's a current store
        if self.state.current_store:
            try:
                store_select.value = self.state.current_store.name
            except Exception:
                pass

    def on_select_changed(self, event: Select.Changed):
        """Handle store selection change."""
        self._selected_store = event.value

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "switch-btn":
            self.switch_store()
        elif button_id == "delete-btn":
            self.delete_store()
        elif button_id == "new-btn":
            self.action_new_store()
        elif button_id == "cancel-btn":
            self.action_cancel()

    def switch_store(self):
        """Switch to selected store."""
        store_select = self.query_one("#store-select", Select)
        store_name = store_select.value

        if not store_name:
            self.query_one("#status", Static).update("Please select a store first.")
            return

        store = self.state.storage.get_store(store_name) if self.state.storage else None
        if store:
            self.state.set_current_store(store)
            self.query_one("#status", Static).update(f"Switched to store: {store_name}")
            self.refresh_stores()
            # Refresh main screen if it exists
            if hasattr(self.app, "refresh_main_screen"):
                self.app.refresh_main_screen()
        else:
            self.query_one("#status", Static).update(f"Store '{store_name}' not found.")

    def delete_store(self):
        """Delete selected store."""
        store_select = self.query_one("#store-select", Select)
        store_name = store_select.value

        if not store_name:
            self.query_one("#status", Static).update("Please select a store first.")
            return

        # Don't allow deleting current store
        if (
            self.state.current_store
            and self.state.current_store.name == store_name
        ):
            self.query_one("#status", Static).update(
                "Cannot delete current store. Switch to another store first."
            )
            return

        if self.state.storage:
            if self.state.storage.delete_store(store_name):
                self.query_one("#status", Static).update(f"Deleted store: {store_name}")
                self.refresh_stores()
            else:
                self.query_one("#status", Static).update(f"Failed to delete store.")

    def action_new_store(self):
        """Create a new store."""
        from zettelkasten.tui.screens.new_store import NewStoreScreen

        def on_dismiss(result):
            """Refresh stores when new store screen is dismissed."""
            self.refresh_stores()

        self.app.push_screen(NewStoreScreen(), callback=on_dismiss)

    def action_cancel(self):
        """Cancel and return to main screen."""
        self.dismiss()

