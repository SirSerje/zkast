"""Main TUI application for Zettelkasten."""
from typing import Optional
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container

from zettelkasten.tui.screens.main_screen import MainScreen
from zettelkasten.state import AppState
from zettelkasten.storage import SQLiteStorage


class ZettelkastenApp(App):
    """Main Textual application."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        margin: 1;
    }
    
    #current-store {
        text-align: center;
        margin: 1;
    }
    
    #status {
        text-align: center;
        margin: 1;
        color: $warning;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #content {
        width: 80;
        height: auto;
        align: center middle;
    }
    
    #store-select-container {
        width: 80;
        height: auto;
        padding: 1;
    }
    
    #new-store-container {
        width: 60;
        height: auto;
        padding: 1;
    }
    
    #entry-editor-container {
        width: 90%;
        height: 90%;
        padding: 1;
    }
    
    .entry-textarea {
        height: 1fr;
        min-height: 10;
        border: solid $primary;
    }
    
    #message-input {
        height: 1fr;
        min-height: 15;
    }
    
    #tags-input {
        width: 100%;
    }
    
    #entry-list-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #entry-log {
        height: 1fr;
    }
    """

    def __init__(self):
        """Initialize the app."""
        super().__init__()
        self._main_screen: Optional[MainScreen] = None

    def compose(self) -> ComposeResult:
        """Compose the app."""
        # Yield a container that will be replaced by the screen
        # Screens are pushed in on_mount
        yield Container(id="app-container")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Zettelkasten"
        self.sub_title = "Note Management"
        
        # Ensure state is initialized
        from zettelkasten.cli import get_zk_path
        try:
            zk_path = get_zk_path()
            if zk_path.exists():
                state = AppState()
                storage = SQLiteStorage(zk_path)
                state.initialize(zk_path, storage)
        except Exception:
            pass  # If initialization fails, screens will handle it
        
        # Push the main screen
        self._main_screen = MainScreen()
        self.push_screen(self._main_screen)

    def refresh_main_screen(self):
        """Refresh the main screen display."""
        if self._main_screen:
            self._main_screen.refresh_display()

