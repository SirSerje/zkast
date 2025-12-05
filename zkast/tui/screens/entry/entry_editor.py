"""Entry editor screen for creating and editing entries."""

from typing import Optional
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Input
from textual.binding import Binding
from datetime import datetime

from zkast.state import AppState
from zkast.models.entry import Entry


class EntryEditorScreen(ModalScreen):
    """Screen for creating new entries."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+c", "quit_with_confirm", "Quit"),
    ]

    def __init__(self, entry: Optional[Entry] = None):
        """Initialize entry editor screen.
        
        Args:
            entry: Optional entry to edit. If None, creates a new entry.
        """
        super().__init__()
        self.state = AppState()
        self._editing_entry = entry
        self._awaiting_quit_confirmation = False

    def compose(self):
        """Compose the screen."""
        title = "Edit Entry" if self._editing_entry else "Create New Entry"
        yield Container(
            Vertical(
                Static(title, id="title"),
                Static("Message (press Tab to move to tags, Ctrl+S to save):", id="message-label"),
                TextArea(
                    id="message-input",
                    language="markdown",
                    classes="entry-textarea",
                    show_line_numbers=False,
                ),
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
        # Populate fields if editing
        if self._editing_entry:
            message_input = self.query_one("#message-input", TextArea)
            tags_input = self.query_one("#tags-input", Input)
            message_input.text = self._editing_entry.message
            tags_input.value = ", ".join(self._editing_entry.tags) if self._editing_entry.tags else ""
        
        self.call_after_refresh(self._focus_textarea)

    def _focus_textarea(self):
        """Focus the text area."""
        try:
            text_area = self.query_one("#message-input", TextArea)
            text_area.focus()
        except Exception:
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

        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        try:
            if self._editing_entry:
                # Update existing entry
                if not self.state.storage:
                    self.query_one("#status", Static).update("Error: No storage available.")
                    return
                
                updated_entry = Entry(
                    id=self._editing_entry.id,
                    store_id=self._editing_entry.store_id,
                    message=message,
                    tags=tags,
                    created_at=self._editing_entry.created_at,
                    updated_at=datetime.now(),
                )
                
                self.state.storage.update_entry(self.state.current_store.name, updated_entry)
                self.state.refresh_entries()
                self.query_one("#status", Static).update("Entry updated successfully.")
            else:
                # Create new entry
                entry = Entry(
                    message=message,
                    tags=tags,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                created_entry = self.state.add_entry(entry)
                self.query_one("#status", Static).update("Entry created successfully.")
            
            if hasattr(self.app, "refresh_main_screen"):
                self.app.refresh_main_screen()
            self.app.set_timer(1.0, self._dismiss_screen)
        except Exception as e:
            self.query_one("#status", Static).update(f"Error: {str(e)}")

    def _dismiss_screen(self):
        """Dismiss the screen."""
        self.dismiss()

    def action_save(self):
        """Save action (keyboard shortcut)."""
        self.save_entry()

    def action_cancel(self):
        """Cancel entry creation."""
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
