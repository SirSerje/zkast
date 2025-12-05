"""Main screen for zkast TUI."""

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Input
from textual.binding import Binding
from textual.events import Key

from zkast.state import AppState
from zkast.tui.components import EntryCard


class MainScreen(Screen):
    """Main screen showing store selection and navigation."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "create_entry", "Create Entry"),
        Binding("d", "delete_selected", "Delete Entry"),
        Binding("up", "scroll_up", "Scroll Up"),
        Binding("down", "scroll_down", "Scroll Down"),
        Binding("e", "edit_selected", "Edit"),
        Binding("z", "navigate_to_card", "Navigate to Card"),
        Binding("ctrl+c", "quit_with_confirm", "Quit"),
    ]

    def __init__(self):
        """Initialize main screen."""
        super().__init__()
        self.state = AppState()
        self._scroll_index = 0  # Start showing from the beginning (latest entries)
        self._selected_card_index = 0  # Index of selected card (0 or 1, relative to displayed cards)
        self._awaiting_quit_confirmation = False
        self._awaiting_navigation = False
        self._navigation_input = None
        self._awaiting_delete_confirmation = False
        self._pending_delete_entry = None

    def compose(self):
        """Compose the screen."""
        yield Header()
        with Vertical(id="main-container"):
            yield Static(
                f"store: {self.state.current_store.name if self.state.current_store else 'None'}",
                id="current-store",
            )
            with Vertical(id="content"):
                yield Container(id="cards-container")
                yield Static("", id="status")
        yield Footer()

    def on_mount(self):
        """Called when screen is mounted."""
        self.refresh_display()
        # Customize footer display
        footer = self.query_one(Footer)
        # Footer automatically shows bindings, but we can customize the highlight
        footer.highlight_key = None

    def refresh_display(self):
        """Refresh the display with current state."""
        current_store_widget = self.query_one("#current-store", Static)
        if self.state.current_store:
            current_store_widget.update(f"store: {self.state.current_store.name}")
        else:
            current_store_widget.update("store: None")
        
        # Reset scroll index and selection when store changes or entries refresh
        self._scroll_index = 0
        self._selected_card_index = 0
        
        # Refresh entries and cards
        self.state.refresh_entries()
        self._refresh_cards()

    def action_create_entry(self):
        """Create a new entry."""
        if not self.state.current_store:
            self.query_one("#status", Static).update(
                "Error: No store selected. Please initialize zkast and create a store first."
            )
            return

        from zkast.tui.screens.entry.entry_editor import EntryEditorScreen

        def on_dismiss(result):
            """Refresh display when entry editor is dismissed."""
            self.refresh_display()

        self.app.push_screen(EntryEditorScreen(), callback=on_dismiss)

    def action_delete_selected(self):
        """Delete the currently selected entry with confirmation."""
        if not self.state.current_store or not self.state.entries:
            return
        
        if self._awaiting_delete_confirmation:
            return
        
        # Get the selected entry
        displayed_count = min(2, len(self.state.entries) - self._scroll_index)
        if self._selected_card_index >= displayed_count:
            return
        
        entry_index = self._scroll_index + self._selected_card_index
        if entry_index >= len(self.state.entries):
            return
        
        selected_entry = self.state.entries[entry_index]
        
        # Show confirmation
        self._pending_delete_entry = selected_entry
        self._awaiting_delete_confirmation = True
        self.query_one("#status", Static).update(
            f"Delete entry {selected_entry.id}? Press 'y' to confirm, 'n' to cancel."
        )

    def _refresh_cards(self):
        """Refresh the entry cards display."""
        cards_container = self.query_one("#cards-container", Container)
        
        # Remove existing cards
        for card in cards_container.query(EntryCard):
            card.remove()
        
        # Add 2 entries starting from scroll_index
        if self.state.current_store and self.state.entries:
            # Ensure scroll_index is within bounds
            max_index = max(0, len(self.state.entries) - 2)
            self._scroll_index = min(self._scroll_index, max_index)
            self._scroll_index = max(0, self._scroll_index)
            
            # Ensure selected_card_index is valid (0 or 1)
            displayed_count = min(2, len(self.state.entries) - self._scroll_index)
            if displayed_count == 0:
                self._selected_card_index = 0
            elif self._selected_card_index >= displayed_count:
                self._selected_card_index = displayed_count - 1
            
            # Get 2 entries starting from scroll_index
            entries = self.state.entries[self._scroll_index:self._scroll_index + 2]
            for i, entry in enumerate(entries):
                is_selected = (i == self._selected_card_index)
                card = EntryCard(entry, selected=is_selected)
                cards_container.mount(card)
    
    def action_scroll_down(self):
        """Scroll down through cards."""
        if not self.state.current_store or not self.state.entries:
            return
        
        displayed_count = min(2, len(self.state.entries) - self._scroll_index)
        
        # If we can move selection down within displayed cards
        if self._selected_card_index < displayed_count - 1:
            self._selected_card_index += 1
            self._refresh_cards()
        else:
            # Move to next pair of cards
            max_index = max(0, len(self.state.entries) - 2)
            if self._scroll_index < max_index:
                self._scroll_index += 1
                self._selected_card_index = 0
                self._refresh_cards()
    
    def action_scroll_up(self):
        """Scroll up through cards."""
        if not self.state.current_store or not self.state.entries:
            return
        
        # If we can move selection up within displayed cards
        if self._selected_card_index > 0:
            self._selected_card_index -= 1
            self._refresh_cards()
        else:
            # Move to previous pair of cards
            if self._scroll_index > 0:
                self._scroll_index -= 1
                displayed_count = min(2, len(self.state.entries) - self._scroll_index)
                self._selected_card_index = displayed_count - 1
                self._refresh_cards()
    
    def action_edit_selected(self):
        """Edit the currently selected card."""
        if not self.state.current_store or not self.state.entries:
            return
        
        # Get the selected entry
        displayed_count = min(2, len(self.state.entries) - self._scroll_index)
        if self._selected_card_index >= displayed_count:
            return
        
        entry_index = self._scroll_index + self._selected_card_index
        if entry_index >= len(self.state.entries):
            return
        
        selected_entry = self.state.entries[entry_index]
        
        # Open editor with the selected entry
        from zkast.tui.screens.entry.entry_editor import EntryEditorScreen
        
        def on_dismiss(result):
            """Refresh display when entry editor is dismissed."""
            self.refresh_display()
        
        # Create editor screen with the entry to edit
        editor = EntryEditorScreen(entry=selected_entry)
        self.app.push_screen(editor, callback=on_dismiss)

    def action_navigate_to_card(self):
        """Start navigation mode to jump to a specific card."""
        if not self.state.current_store or not self.state.entries:
            self.query_one("#status", Static).update("No entries available.")
            return
        
        if self._awaiting_navigation:
            return
        
        self._awaiting_navigation = True
        self.query_one("#status", Static).update(f"Enter card number (1-{len(self.state.entries)}), then press Enter:")
        
        # Create a hidden input for navigation
        nav_input = Input(placeholder="Card number", id="nav-input")
        nav_input.display = False
        self.mount(nav_input)
        self._navigation_input = nav_input
        nav_input.focus()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle navigation input submission."""
        if event.input.id == "nav-input" and self._awaiting_navigation:
            try:
                card_number = int(event.input.value.strip())
                if card_number < 1 or card_number > len(self.state.entries):
                    self.query_one("#status", Static).update(
                        f"Invalid card number. Please enter a number between 1 and {len(self.state.entries)}."
                    )
                    event.input.remove()
                    self._awaiting_navigation = False
                    self._navigation_input = None
                    return
                
                # Convert to 0-based index
                entry_index = card_number - 1
                
                # Calculate scroll_index and selected_card_index
                # We want to show 2 cards, so if entry_index is even, it's the first card
                # If odd, it's the second card
                if entry_index % 2 == 0:
                    # Even index: show as first card
                    self._scroll_index = entry_index
                    self._selected_card_index = 0
                else:
                    # Odd index: show as second card
                    self._scroll_index = entry_index - 1
                    self._selected_card_index = 1
                
                # Ensure scroll_index is within bounds
                max_index = max(0, len(self.state.entries) - 2)
                self._scroll_index = min(self._scroll_index, max_index)
                self._scroll_index = max(0, self._scroll_index)
                
                self._refresh_cards()
                self.query_one("#status", Static).update(f"Navigated to card {card_number}.")
                event.input.remove()
                self._awaiting_navigation = False
                self._navigation_input = None
            except ValueError:
                self.query_one("#status", Static).update("Please enter a valid number.")
                event.input.remove()
                self._awaiting_navigation = False
                self._navigation_input = None

    def action_quit(self):
        """Quit the application."""
        self.app.exit()
    
    def action_quit_with_confirm(self):
        """Show quit confirmation."""
        if self._awaiting_quit_confirmation:
            return
        
        self.query_one("#status", Static).update("Are you sure you want to quit? Press 'q' to confirm, Esc to cancel.")
        self._awaiting_quit_confirmation = True
    
    def on_key(self, event: Key):
        """Handle key presses for quit confirmation, delete confirmation, and navigation cancellation."""
        if self._awaiting_delete_confirmation:
            if event.key == "y":
                # Confirm deletion
                if self._pending_delete_entry and self.state.storage:
                    try:
                        if self.state.storage.delete_entry(
                            self.state.current_store.name,
                            self._pending_delete_entry.id
                        ):
                            self.query_one("#status", Static).update(
                                f"Entry {self._pending_delete_entry.id} deleted."
                            )
                            self.refresh_display()
                        else:
                            self.query_one("#status", Static).update("Failed to delete entry.")
                    except Exception as e:
                        self.query_one("#status", Static).update(f"Error: {str(e)}")
                self._awaiting_delete_confirmation = False
                self._pending_delete_entry = None
                event.prevent_default()
                return
            elif event.key == "n" or event.key == "escape":
                # Cancel deletion
                self.query_one("#status", Static).update("Deletion cancelled.")
                self._awaiting_delete_confirmation = False
                self._pending_delete_entry = None
                event.prevent_default()
                return
        
        if self._awaiting_navigation:
            if event.key == "escape":
                # Cancel navigation
                if self._navigation_input:
                    self._navigation_input.remove()
                    self._navigation_input = None
                self._awaiting_navigation = False
                self.query_one("#status", Static).update("")
                event.prevent_default()
                return
        
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
        
        # Let other keys be handled normally

