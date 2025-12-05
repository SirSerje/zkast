"""Store selection screen for zkast TUI."""

from typing import Optional
from textual.screen import ModalScreen
from textual.containers import Container, Vertical
from textual.widgets import Static, ListView, ListItem, Label
from textual.binding import Binding
from textual.message import Message
from textual.events import Key

from zkast.state import AppState
from zkast.models.store import Store


class StoreSelectScreen(ModalScreen):
    """Screen for selecting, switching, and deleting stores."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("n", "new_store", "New Store"),
        Binding("enter", "select_store", "Select"),
        Binding("d", "delete_store", "Delete"),
        Binding("ctrl+c", "quit_with_confirm", "Quit"),
    ]

    def __init__(self):
        """Initialize store select screen."""
        super().__init__()
        self.state = AppState()
        self._selected_index: Optional[int] = None
        self._awaiting_confirmation = False
        self._pending_delete: Optional[str] = None
        self._awaiting_quit_confirmation = False

    def compose(self):
        """Compose the screen."""
        yield Container(
            Vertical(
                Static("Store Management", id="title"),
                Static("Use ↑↓ to navigate, Enter to select/create, 'd' to delete, 'n' to create, Esc to cancel", id="help-text"),
                Static("", id="status"),
                ListView(id="store-list"),
                id="store-select-container",
            )
        )

    def on_mount(self):
        """Called when screen is mounted."""
        self.refresh_stores()
        # Focus the list view
        self.call_after_refresh(lambda: self.query_one("#store-list", ListView).focus())
    

    def refresh_stores(self):
        """Refresh the store list."""
        self.state.refresh_stores()
        store_list = self.query_one("#store-list", ListView)
        
        # Remove all items by iterating through children and removing them
        # This ensures they're fully removed before adding new ones
        while store_list.children:
            child = store_list.children[0]
            child.remove()
        
        # Small delay to ensure removal completes, then add new items
        def add_new_items():
            # Add stores as list items
            for store in self.state.stores:
                is_current = self.state.current_store and self.state.current_store.name == store.name
                label_text = f"{'* ' if is_current else '  '}{store.name} ({store.format})"
                item = ListItem(Label(label_text), id=f"store-{store.name}")
                store_list.append(item)
            
            # Add "Create New Store" option at the end
            create_item = ListItem(Label("+ Create New Store"), id="create-store")
            store_list.append(create_item)
            
            # Set initial selection (there's always at least the "Create New Store" item)
            try:
                store_list.index = 0
            except Exception:
                pass
        
        self.app.set_timer(0.05, add_new_items)

    def action_select_store(self):
        """Select the currently highlighted store."""
        # Don't allow selection if awaiting confirmation
        if self._awaiting_confirmation:
            return
            
        store_list = self.query_one("#store-list", ListView)
        if store_list.highlighted_child is None:
            self.query_one("#status", Static).update("Please select a store first.")
            return
        
        # Get the highlighted item
        highlighted_item = store_list.highlighted_child
        
        # Check if it's the "Create New Store" option
        if highlighted_item.id == "create-store":
            self.action_new_store()
            return
        
        # Make sure it's a store item (not create-store)
        if not highlighted_item.id.startswith("store-"):
            return
        
        # Get the store name from the highlighted item
        store_name = highlighted_item.id.replace("store-", "")
        
        store = self.state.storage.get_store(store_name) if self.state.storage else None
        if store:
            self.state.set_current_store(store)
            self.query_one("#status", Static).update(f"Switched to store: {store_name}")
            if hasattr(self.app, "refresh_main_screen"):
                self.app.refresh_main_screen()
            self.dismiss(None)
        else:
            self.query_one("#status", Static).update(f"Store '{store_name}' not found.")

    def action_delete_store(self):
        """Delete the currently highlighted store with confirmation."""
        # If already awaiting confirmation, ignore
        if self._awaiting_confirmation:
            return
            
        store_list = self.query_one("#store-list", ListView)
        if store_list.highlighted_child is None:
            self.query_one("#status", Static).update("Please select a store first.")
            return
        
        # Get the highlighted item
        highlighted_item = store_list.highlighted_child
        
        # Can't delete the "Create New Store" option
        if highlighted_item.id == "create-store":
            self.query_one("#status", Static).update("Cannot delete 'Create New Store' option.")
            return
        
        # Get the store name from the highlighted item
        if not highlighted_item.id.startswith("store-"):
            self.query_one("#status", Static).update("Please select a store to delete.")
            return
        
        store_name = highlighted_item.id.replace("store-", "")
        
        if self.state.current_store and self.state.current_store.name == store_name:
            self.query_one("#status", Static).update(
                "Cannot delete current store. Switch to another store first."
            )
            return
        
        # Show confirmation message
        status_widget = self.query_one("#status", Static)
        status_widget.update(f"Delete '{store_name}'? Press 'y' to confirm, 'n' or Esc to cancel.")
        
        # Set up confirmation state
        self._pending_delete = store_name
        self._awaiting_confirmation = True

    def on_key(self, event: Key):
        """Handle key presses for confirmation."""
        # Handle quit confirmation first
        if self._awaiting_quit_confirmation:
            if event.key == "q":
                # Confirm quit
                self.app.exit()
                event.prevent_default()
                return
            elif event.key == "escape":
                # Cancel quit
                self.query_one("#status", Static).update("Quit cancelled.")
                self._awaiting_quit_confirmation = False
                self.query_one("#store-list", ListView).focus()
                event.prevent_default()
                return
        
        # Handle deletion confirmation
        if self._awaiting_confirmation:
            if event.key == "y":
                # Confirm deletion
                store_name = self._pending_delete
                if store_name and self.state.storage:
                    try:
                        if self.state.storage.delete_store(store_name):
                            self.query_one("#status", Static).update(f"Deleted store: {store_name}")
                            # Refresh stores after a delay to ensure deletion is complete
                            self.app.set_timer(0.3, lambda: self.refresh_stores())
                        else:
                            self.query_one("#status", Static).update(f"Failed to delete store.")
                    except Exception as e:
                        self.query_one("#status", Static).update(f"Error deleting store: {str(e)}")
                self._awaiting_confirmation = False
                self._pending_delete = None
                # Refocus the list after a delay
                self.app.set_timer(0.2, lambda: self.query_one("#store-list", ListView).focus())
                event.prevent_default()
                return
            elif event.key == "n":
                # Cancel deletion - prevent it from triggering new_store action
                self.query_one("#status", Static).update("Deletion cancelled.")
                self._awaiting_confirmation = False
                self._pending_delete = None
                # Refocus the list
                self.query_one("#store-list", ListView).focus()
                event.prevent_default()
                return
            elif event.key == "escape":
                # Cancel deletion
                self.query_one("#status", Static).update("Deletion cancelled.")
                self._awaiting_confirmation = False
                self._pending_delete = None
                # Refocus the list
                self.query_one("#store-list", ListView).focus()
                event.prevent_default()
                return
        
        # Handle Ctrl+C for quit confirmation (only if not in other confirmation modes)
        if event.key == "ctrl+c":
            self.action_quit_with_confirm()
            event.prevent_default()
            return
        
        # Don't intercept other keys - let them be handled by bindings and ListView
        # This allows arrow keys, enter, escape, etc. to work normally via bindings
    
    def action_quit_with_confirm(self):
        """Show quit confirmation."""
        if self._awaiting_confirmation or self._awaiting_quit_confirmation:
            return
        
        self.query_one("#status", Static).update("Are you sure you want to quit? Press 'q' to confirm, Esc to cancel.")
        self._awaiting_quit_confirmation = True

    def action_new_store(self):
        """Create a new store."""
        # Don't allow creating new store if awaiting deletion or quit confirmation
        if self._awaiting_confirmation or self._awaiting_quit_confirmation:
            return
            
        from zkast.tui.screens.new_store import NewStoreScreen

        def on_dismiss(result):
            """Refresh stores when new store screen is dismissed."""
            # Check if a store was created
            store_created = self.state.current_store is not None
            
            # Refresh stores list after a short delay to ensure screen is ready
            def refresh_after_delay():
                try:
                    self.refresh_stores()
                    # Refocus the list
                    store_list = self.query_one("#store-list", ListView)
                    store_list.focus()
                except Exception:
                    pass
                
                # If a store was created, dismiss this screen too
                if store_created:
                    try:
                        self.dismiss(None)
                    except Exception:
                        pass
            
            self.app.set_timer(0.2, refresh_after_delay)

        self.app.push_screen(NewStoreScreen(), callback=on_dismiss)

    def action_cancel(self):
        """Cancel and return to main screen."""
        # If awaiting confirmation, cancel that first
        if self._awaiting_confirmation:
            self.query_one("#status", Static).update("Deletion cancelled.")
            self._awaiting_confirmation = False
            self._pending_delete = None
            self.query_one("#store-list", ListView).focus()
            return
        
        # Dismiss the modal screen to return to main screen
        self.dismiss(None)
