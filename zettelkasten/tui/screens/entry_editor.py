"""Entry editor screen for creating entries."""
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input
from textual.binding import Binding
from datetime import datetime

from zettelkasten.state import AppState
from zettelkasten.models.entry import Entry


class EntryEditorScreen(ModalScreen):
    """Screen for creating new entries."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self):
        """Initialize entry editor screen."""
        super().__init__()
        self.state = AppState()

    def compose(self):
        """Compose the screen."""
        yield Container(
            Vertical(
                Static("Create New Entry", id="title"),
                Static("Message (press Tab to move to tags, Ctrl+S to save):", id="message-label"),
                TextArea(id="message-input", language="markdown", classes="entry-textarea", show_line_numbers=False),
                Static("Tags (comma-separated):", id="tags-label"),
                Input(placeholder="tag1, tag2, tag3", id="tags-input"),
                Static("", id="status"),
                Horizontal(
                    Button("Save", id="save-btn", variant="primary"),
                    Button("Cancel", id="cancel-btn"),
                ),
                id="entry-editor-container",
            )
        )

    def on_mount(self):
        """Called when screen is mounted."""
        # Focus the text area after screen is fully mounted
        # Use call_after_refresh to ensure the widget is ready
        self.call_after_refresh(self._focus_textarea)
    
    def _focus_textarea(self):
        """Focus the text area."""
        try:
            text_area = self.query_one("#message-input", TextArea)
            text_area.focus()
        except Exception:
            # If focus fails, try again after a short delay
            self.set_timer(0.2, self._focus_textarea)

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-btn":
            self.save_entry()
        elif button_id == "cancel-btn":
            self.action_cancel()

    def save_entry(self):
        """Save the entry."""
        message_input = self.query_one("#message-input", TextArea)
        tags_input = self.query_one("#tags-input", Input)

        message = message_input.text.strip()
        tags_str = tags_input.value.strip()

        if not message:
            self.query_one("#status", Static).update("Message cannot be empty.")
            return

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        # Create entry
        entry = Entry(
            message=message,
            tags=tags,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        try:
            created_entry = self.state.add_entry(entry)
            self.query_one("#status", Static).update("Entry created successfully.")
            # Refresh main screen if it exists
            if hasattr(self.app, "refresh_main_screen"):
                self.app.refresh_main_screen()
            # Dismiss after a brief delay - schedule outside of message handler
            self.app.set_timer(1.0, self._dismiss_screen)
        except Exception as e:
            self.query_one("#status", Static).update(f"Error: {str(e)}")
    
    def _dismiss_screen(self):
        """Dismiss the screen (called from timer, not message handler)."""
        self.dismiss()

    def action_save(self):
        """Save action (keyboard shortcut)."""
        self.save_entry()

    def action_cancel(self):
        """Cancel entry creation."""
        self.dismiss()

