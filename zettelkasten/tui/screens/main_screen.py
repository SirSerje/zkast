"""Main screen for Zettelkasten TUI."""
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding

from zettelkasten.state import AppState


class MainScreen(Screen):
    """Main screen showing store selection and navigation."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "show_stores", "Stores"),
        Binding("c", "create_entry", "Create Entry"),
        Binding("d", "debug_view", "Debug View"),
    ]

    def __init__(self):
        """Initialize main screen."""
        super().__init__()
        self.state = AppState()

    def compose(self):
        """Compose the screen."""
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="content"):
                yield Static("Zettelkasten", id="title")
                yield Static(
                    f"Current Store: {self.state.current_store.name if self.state.current_store else 'None'}",
                    id="current-store",
                )
                yield Static("", id="status")
        yield Footer()

    def on_mount(self):
        """Called when screen is mounted."""
        self.refresh_display()

    def refresh_display(self):
        """Refresh the display with current state."""
        current_store_widget = self.query_one("#current-store", Static)
        if self.state.current_store:
            current_store_widget.update(
                f"Current Store: {self.state.current_store.name}"
            )
        else:
            current_store_widget.update("Current Store: None")

    def action_show_stores(self):
        """Show store selection screen."""
        from zettelkasten.tui.screens.store_select import StoreSelectScreen

        def on_dismiss(result):
            """Refresh display when store selection screen is dismissed."""
            self.refresh_display()

        self.app.push_screen(StoreSelectScreen(), callback=on_dismiss)

    def action_create_entry(self):
        """Create a new entry."""
        if not self.state.current_store:
            self.query_one("#status", Static).update(
                "Error: No store selected. Please select a store first."
            )
            return

        from zettelkasten.tui.screens.entry_editor import EntryEditorScreen

        def on_dismiss(result):
            """Refresh display when entry editor is dismissed."""
            self.refresh_display()

        self.app.push_screen(EntryEditorScreen(), callback=on_dismiss)

    def action_debug_view(self):
        """Show debug view."""
        if not self.state.current_store:
            self.query_one("#status", Static).update(
                "Error: No store selected. Please select a store first."
            )
            return

        from zettelkasten.tui.screens.entry_list import EntryListScreen

        self.app.push_screen(EntryListScreen())

    def action_quit(self):
        """Quit the application."""
        self.app.exit()

