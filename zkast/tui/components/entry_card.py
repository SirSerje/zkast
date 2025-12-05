"""Entry card component for displaying entries in a card format."""

from datetime import datetime
from textual.widget import Widget
from textual.containers import Container, Vertical
from textual.widgets import Static
from typing import Optional

from zkast.models.entry import Entry


class EntryCard(Widget):
    """A card component that displays an entry in a paper card style."""

    DEFAULT_CSS = """
    EntryCard {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        padding-top: 0;
        margin: 1;
        background: $surface;
    }
    
    EntryCard.selected {
        border: solid $accent;
    }
    
    EntryCard > Container {
        width: 100%;
        height: auto;
    }
    
    EntryCard #card-id {
        text-align: left;
        text-style: bold;
        color: $primary;
        margin-bottom: 0;
        height: auto;
    }
    
    EntryCard #card-body {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
    }
    
    EntryCard #card-footer {
        width: 100%;
        height: auto;
        margin-top: 0;
        padding-top: 0;
        border-top: solid $primary;
    }
    
    EntryCard #card-tags {
        text-align: left;
        color: $accent;
        margin-top: 0;
        margin-bottom: 0;
        height: auto;
    }
    
    EntryCard #card-date {
        text-align: left;
        color: $text-muted;
        margin-top: 0;
        margin-bottom: 0;
        height: auto;
    }
    """

    def __init__(self, entry: Entry, selected: bool = False):
        """Initialize entry card with an entry."""
        super().__init__()
        self.entry = entry
        if selected:
            self.add_class("selected")

    def compose(self):
        """Compose the card layout."""
        with Container():
            # ID on top
            yield Static(f"#{self.entry.id}", id="card-id")
            
            # Body text
            yield Static(self._format_body(), id="card-body")
            
            # Footer with tags and date
            with Vertical(id="card-footer"):
                # Tags
                tags_text = ", ".join(self.entry.tags) if self.entry.tags else "No tags"
                yield Static(f"Tags: {tags_text}", id="card-tags")
                
                # Date (under tags)
                date_text = self._format_date()
                yield Static(date_text, id="card-date")

    def _format_body(self) -> str:
        """Format the body text, truncating if too long."""
        max_lines = 5
        lines = self.entry.message.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + "\n..."
        return self.entry.message

    def _format_date(self) -> str:
        """Format the date as DD-MM-YYYY HH-MM."""
        if not self.entry.updated_at:
            return "No date"
        
        dt = self.entry.updated_at
        if isinstance(dt, str):
            # Parse if it's a string
            try:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except Exception:
                return "Invalid date"
        
        return dt.strftime("%d-%m-%Y %H-%M")

