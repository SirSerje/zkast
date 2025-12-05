"""Main TUI application for zkast."""

from typing import Optional
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container

from zkast.tui.screens.dashboard.main_screen import MainScreen
from zkast.state import AppState
from zkast.storage import SQLiteStorage


class ZkastApp(App):
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
    
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #current-store {
        text-align: left;
        height: 1;
        width: 100%;
        padding-left: 1;
    }
    
    #content {
        width: 100%;
        height: 1fr;
    }
    
    #status {
        text-align: center;
        margin: 1;
        color: $warning;
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
    
    #cards-container {
        width: 100%;
        height: auto;
        padding: 1;
        margin: 1;
    }
    
    #store-list {
        height: 20;
        border: solid $primary;
        padding: 1;
    }
    
    #help-text {
        text-align: center;
        color: $text-muted;
        margin: 1;
    }
    
    Footer {
        text-align: center;
    }
    
    #custom-footer {
        width: 100%;
        height: 1;
        text-align: center;
        background: $surface;
        border-top: solid $primary;
        dock: bottom;
    }
    """

    def __init__(self):
        """Initialize the app."""
        super().__init__()
        self._main_screen: Optional[MainScreen] = None

    def compose(self) -> ComposeResult:
        """Compose the app."""
        yield Container(id="app-container")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "zkast"
        self.sub_title = "Note Management"

        from zkast.cli import get_zkast_path

        try:
            zkast_path = get_zkast_path()
            # Initialize even if zkast_path doesn't exist yet - user can create stores
            state = AppState()
            if zkast_path.exists():
                storage = SQLiteStorage(zkast_path)
                state.initialize(zkast_path, storage)
            else:
                # Initialize with empty state - user can create stores via TUI
                zkast_path.mkdir(parents=True, exist_ok=True)
                storage = SQLiteStorage(zkast_path)
                state.initialize(zkast_path, storage)
        except Exception:
            # If initialization fails, still allow TUI to start
            # User can create stores via the TUI
            pass

        self._main_screen = MainScreen()
        self.push_screen(self._main_screen)

    def refresh_main_screen(self):
        """Refresh the main screen display."""
        if self._main_screen:
            self._main_screen.refresh_display()
