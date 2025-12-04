"""Entry list screen for debug view."""
from textual.screen import ModalScreen
from textual.containers import Container, Vertical
from textual.widgets import Static, RichLog
from textual.binding import Binding

from zettelkasten.state import AppState


class EntryListScreen(ModalScreen):
    """Screen for viewing all entries (debug view)."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    def __init__(self):
        """Initialize entry list screen."""
        super().__init__()
        self.state = AppState()

    def compose(self):
        """Compose the screen."""
        yield Container(
            Vertical(
                Static("Debug View - All Entries", id="title"),
                RichLog(id="entry-log", wrap=True),
                Static("Press 'q' or 'Esc' to close", id="help"),
                id="entry-list-container",
            )
        )

    def on_mount(self):
        """Called when screen is mounted."""
        self.refresh_entries()

    def refresh_entries(self):
        """Refresh and display entries."""
        self.state.refresh_entries()
        entry_log = self.query_one("#entry-log", RichLog)

        if not self.state.entries:
            entry_log.write("No entries found.")
            return

        entry_log.write(f"Total entries: {len(self.state.entries)}\n")
        entry_log.write("=" * 80 + "\n")

        for entry in self.state.entries:
            entry_log.write(f"\nEntry ID: {entry.id}")
            entry_log.write(f"Created: {entry.created_at}")
            entry_log.write(f"Updated: {entry.updated_at}")
            entry_log.write(f"Tags: {', '.join(entry.tags) if entry.tags else 'None'}")
            entry_log.write(f"Message:\n{entry.message}")
            entry_log.write("=" * 80 + "\n")

    def action_close(self):
        """Close the debug view."""
        self.dismiss()

