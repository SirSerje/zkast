"""New store creation screen."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Select
from textual.binding import Binding

from zkast.state import AppState


class NewStoreScreen(ModalScreen):
    """Screen for creating a new store."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "quit_with_confirm", "Quit"),
    ]

    def __init__(self):
        """Initialize new store screen."""
        super().__init__()
        self.state = AppState()
        self._awaiting_quit_confirmation = False

    def compose(self):
        """Compose the screen."""
        yield Container(
            Vertical(
                Static("Create New Store", id="title"),
                Static("Store Name:", id="name-label"),
                Input(placeholder="Enter store name", id="name-input"),
                Static("Storage Format:", id="format-label"),
                Select(
                    [("SQLite", "sqlite")],
                    value="sqlite",
                    id="format-select",
                ),
                Static("", id="status"),
                Horizontal(
                    Button("Create", id="create-btn", variant="primary"),
                    Button("Cancel", id="cancel-btn"),
                ),
                id="new-store-container",
            )
        )

    def on_mount(self):
        """Called when screen is mounted."""
        self.query_one("#name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        if event.input.id == "name-input":
            self.create_store()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "create-btn":
            self.create_store()
        elif button_id == "cancel-btn":
            self.action_cancel()

    def create_store(self):
        """Create a new store."""
        name_input = self.query_one("#name-input", Input)
        format_select = self.query_one("#format-select", Select)

        store_name = name_input.value.strip()
        if isinstance(format_select.value, str):
            store_format = format_select.value
        else:
            store_format = "sqlite"

        if not store_name:
            self.query_one("#status", Static).update("Store name cannot be empty.")
            return

        if not self.state.storage:
            # Try to initialize storage if not already initialized
            from zkast.cli import get_zkast_path
            from zkast.storage import SQLiteStorage
            
            try:
                zkast_path = get_zkast_path()
                zkast_path.mkdir(parents=True, exist_ok=True)
                storage = SQLiteStorage(zkast_path)
                self.state.initialize(zkast_path, storage)
            except Exception as e:
                self.query_one("#status", Static).update(f"Failed to initialize storage: {str(e)}")
                return

        try:
            store = self.state.storage.create_store(store_name, store_format)
            self.state.set_current_store(store)
            self.query_one("#status", Static).update(f"Store '{store_name}' created successfully.")
            # Refresh main screen if it exists
            if hasattr(self.app, "refresh_main_screen"):
                try:
                    self.app.refresh_main_screen()
                except Exception:
                    pass
            # Dismiss after a short delay
            self.app.set_timer(0.5, self._dismiss_screen)
        except ValueError as e:
            self.query_one("#status", Static).update(str(e))
        except Exception as e:
            self.query_one("#status", Static).update(f"Error creating store: {str(e)}")

    def _dismiss_screen(self):
        """Dismiss the screen."""
        self.dismiss()

    def action_cancel(self):
        """Cancel store creation."""
        self.dismiss()
    
    def action_quit_with_confirm(self):
        """Show quit confirmation."""
        if self._awaiting_quit_confirmation:
            return
        
        self.query_one("#status", Static).update("Are you sure you want to quit? Press 'q' to confirm, Esc to cancel.")
        self._awaiting_quit_confirmation = True
    
    def on_key(self, event):
        """Handle key presses for quit confirmation."""
        if self._awaiting_quit_confirmation:
            if event.key == "q":
                # Confirm quit
                self.app.exit()
                event.prevent_default()
                return
            elif event.key == "escape":
                # Cancel quit
                self.query_one("#status", Static).update("")
                self._awaiting_quit_confirmation = False
                event.prevent_default()
                return
        
        # Handle Ctrl+C
        if event.key == "ctrl+c":
            self.action_quit_with_confirm()
            event.prevent_default()
            return
        
        # Let other keys be handled normally
