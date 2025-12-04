"""New store creation screen."""
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Select
from textual.binding import Binding

from zettelkasten.state import AppState


class NewStoreScreen(ModalScreen):
    """Screen for creating a new store."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self):
        """Initialize new store screen."""
        super().__init__()
        self.state = AppState()

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
                    prompt="Select format",
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
        store_format = format_select.value or "sqlite"

        if not store_name:
            self.query_one("#status", Static).update("Store name cannot be empty.")
            return

        if not self.state.storage:
            self.query_one("#status", Static).update("Storage not initialized.")
            return

        try:
            store = self.state.storage.create_store(store_name, store_format)
            self.state.set_current_store(store)
            self.query_one("#status", Static).update(
                f"Store '{store_name}' created successfully."
            )
            # Refresh main screen if it exists
            if hasattr(self.app, "refresh_main_screen"):
                self.app.refresh_main_screen()
            # Dismiss after a brief delay - schedule outside of message handler
            self.app.set_timer(1.0, self._dismiss_screen)
        except ValueError as e:
            self.query_one("#status", Static).update(str(e))

    def _dismiss_screen(self):
        """Dismiss the screen (called from timer, not message handler)."""
        self.dismiss()

    def action_cancel(self):
        """Cancel store creation."""
        self.dismiss()

