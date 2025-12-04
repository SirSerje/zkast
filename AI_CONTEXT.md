# AI Context Documentation for Zettelkasten CLI

This document provides comprehensive context for AI assistants working on this codebase.

## Project Overview

Zettelkasten CLI is a Python 3 command-line tool for managing notes using the Zettelkasten method. The application follows a layered architecture with strict separation of concerns and loose coupling between layers.

## Version

Current version: **0.1.0**

## Architecture Layers

### 1. Storage Layer (`zettelkasten/storage/`)

**Purpose**: Abstract data persistence using strategy pattern for easy replacement.

**Key Files**:
- `base.py` - `StorageInterface` abstract base class
- `sqlite_storage.py` - `SQLiteStorage` implementation

**Interface Methods**:
- `create_store(name: str, format: str) -> Store`
- `list_stores() -> List[Store]`
- `get_store(name: str) -> Optional[Store]`
- `delete_store(name: str) -> bool`
- `create_entry(store_name: str, entry: Entry) -> Entry`
- `list_entries(store_name: str) -> List[Entry]`

**Design Principles**:
- Storage layer only knows about models, not TUI or state
- Easy to swap SQLite for another storage backend
- Each store has its own database file: `.zettelkasten/{store_name}.db`
- Metadata stored in `.zettelkasten/metadata.db`

**Database Schema**:
```sql
-- Metadata (metadata.db)
stores: id, name (UNIQUE), format, created_at

-- Per-store database ({store_name}.db)
entries: id, store_id, message, created_at, updated_at
tags: id, name (UNIQUE)
entry_tags: entry_id, tag_id (junction table)
```

### 2. Models Layer (`zettelkasten/models/`)

**Purpose**: Data validation and structure using Pydantic.

**Key Files**:
- `store.py` - `Store` model
- `entry.py` - `Entry` model

**Store Model**:
```python
Store(id, name, format, created_at)
```

**Entry Model**:
```python
Entry(id, store_id, message, tags: List[str], created_at, updated_at)
```

**Design Principles**:
- Pydantic models for validation
- JSON serialization support
- Type-safe data structures

### 3. State Layer (`zettelkasten/state.py`)

**Purpose**: Single source of truth for application state (singleton pattern).

**Key Properties**:
- `current_store: Optional[Store]` - Currently active store
- `stores: List[Store]` - All available stores
- `entries: List[Entry]` - Entries from current store
- `storage: Optional[StorageInterface]` - Storage instance

**Key Methods**:
- `initialize(base_path: Path, storage: StorageInterface)` - Initialize state
- `refresh_stores()` - Reload stores from storage
- `set_current_store(store: Store)` - Switch store and load entries
- `refresh_entries()` - Reload entries from current store
- `add_entry(entry: Entry)` - Add entry to current store

**State Persistence**:
- Current store name saved to `.zettelkasten/.state.json`
- Loaded on initialization
- Updated when store changes

**Design Principles**:
- Singleton pattern ensures single instance
- State only knows about models, not TUI or controls
- State mutations happen through methods, not direct property access

### 4. Controls Layer (`zettelkasten/controls.py`)

**Purpose**: Orchestrate user interactions and coordinate state/storage operations.

**Key Methods**:
- `create_store(name: str, format: str) -> Store`
- `list_stores() -> List[Store]`
- `switch_store(name: str) -> bool`
- `delete_store(name: str) -> bool`
- `create_entry(message: str, tags: List[str]) -> Entry`
- `list_entries() -> List[Entry]`

**Design Principles**:
- Controls orchestrate state + storage
- Handles business logic and validation
- Future API endpoints would be added here
- TUI calls controls, controls modify state/storage

### 5. TUI Layer (`zettelkasten/tui/`)

**Purpose**: Textual-based terminal user interface for rendering and interaction.

**Key Files**:
- `app.py` - `ZettelkastenApp` main application
- `screens/main_screen.py` - Main navigation screen
- `screens/store_select.py` - Store management screen
- `screens/new_store.py` - Store creation screen
- `screens/entry_editor.py` - Entry creation/editing screen
- `screens/entry_list.py` - Debug view screen

**Screen Hierarchy**:
```
ZettelkastenApp
  └── MainScreen (default)
      ├── StoreSelectScreen (modal)
      │   └── NewStoreScreen (modal)
      ├── EntryEditorScreen (modal)
      └── EntryListScreen (modal)
```

**Keyboard Bindings**:
- Main: `s` (stores), `c` (create), `d` (debug), `q` (quit)
- Store Select: `n` (new), `Esc` (cancel)
- Entry Editor: `Ctrl+S` (save), `Esc` (cancel)
- Entry List: `q`/`Esc` (close)

**Design Principles**:
- TUI only renders state, doesn't modify it directly
- Screens observe state changes
- User actions trigger controls layer methods
- Modal screens for focused interactions

### 6. CLI Layer (`zettelkasten/cli.py`)

**Purpose**: Command-line interface using Click framework.

**Commands**:
- `zk init` - Initialize zettelkasten
- `zk store list` - List stores
- `zk store switch <name>` - Switch store
- `zk store delete <name>` - Delete store
- `zk entry create` - Create entry (TUI)
- `zk debug-view` - Show all entries
- `zk tui` - Launch full TUI

**Helper Functions**:
- `get_zk_path() -> Path` - Get `.zettelkasten/` directory
- `ensure_initialized() -> tuple[AppState, Controls]` - Ensure init, return state/controls

**Design Principles**:
- CLI commands initialize state/storage as needed
- Rich console for formatted output
- TUI launched for interactive operations

## Data Flow

### Creating an Entry (TUI)
1. User presses `c` on MainScreen
2. MainScreen checks if store selected
3. MainScreen pushes EntryEditorScreen
4. User fills form and saves
5. EntryEditorScreen calls `state.add_entry()`
6. State calls `storage.create_entry()`
7. Storage persists to SQLite
8. State updates entries list
9. Screen dismisses, MainScreen refreshes

### Creating an Entry (CLI)
1. User runs `zk entry create`
2. CLI ensures initialized
3. CLI checks if store selected
4. CLI launches TUI app
5. Same flow as TUI above

### Switching Store
1. User selects store in StoreSelectScreen
2. Screen calls `state.set_current_store()`
3. State calls `storage.list_entries()`
4. State updates current_store and entries
5. State saves to `.state.json`
6. Screen refreshes, MainScreen refreshes

## File Locations

### Configuration
- `.zettelkasten/` - Base directory (created by `zk init`)
- `.zettelkasten/metadata.db` - Store metadata
- `.zettelkasten/{store_name}.db` - Per-store databases
- `.zettelkasten/.state.json` - Current state persistence

### Code Organization
- All code in `zettelkasten/` package
- Tests in `tests/` directory
- Requirements in `requirements.txt` and `requirements-dev.txt`

## Dependencies

**Core**:
- `click>=8.0.0` - CLI framework
- `pydantic>=2.0.0` - Data validation
- `textual>=0.40.0` - TUI framework
- `rich>=13.0.0` - Terminal formatting

**Development**:
- `pytest>=7.0.0` - Testing
- `black>=23.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking
- `pyinstaller>=5.0.0` - Bundling

## Adding New Features

### Adding a New Storage Backend

1. Create new file in `zettelkasten/storage/` (e.g., `postgres_storage.py`)
2. Implement `StorageInterface` from `base.py`
3. Update CLI `init` command to offer new format
4. Storage selection happens at initialization

### Adding a New TUI Screen

1. Create screen class inheriting from `Screen` or `ModalScreen`
2. Add to `screens/` directory
3. Add navigation from existing screen
4. Screen should observe state, call controls for mutations

### Adding a New CLI Command

1. Add command function to `cli.py`
2. Use `ensure_initialized()` to get state/controls
3. Call appropriate controls method
4. Use Rich console for output

### Adding API Endpoints (Future)

1. Add methods to `Controls` class
2. Create API layer that calls controls
3. API layer should not directly access state/storage
4. Follow same patterns as TUI layer

## Common Patterns

### State Initialization
```python
state = AppState()
storage = SQLiteStorage(zk_path)
state.initialize(zk_path, storage)
controls = Controls(state, storage)
```

### Error Handling
- Storage layer raises `ValueError` for invalid operations
- CLI catches exceptions and displays user-friendly messages
- TUI screens show status messages for errors

### State Refresh
- Call `state.refresh_stores()` after store operations
- Call `state.refresh_entries()` after entry operations
- TUI screens call `refresh_display()` after state changes

## Testing Strategy

- Unit tests for storage layer (test SQLite operations)
- Unit tests for models (test validation)
- Integration tests for state layer
- E2E tests for CLI commands
- TUI tests using Textual's testing utilities

## Version 0.1.0 Features

✅ Initialize zettelkasten
✅ Store selection (SQLite only, but choice presented)
✅ Store management (list, switch, delete)
✅ Entry creation with message and tags
✅ Debug view showing all entries
✅ TUI interface for all operations
✅ State persistence

## Future Enhancements

- Entry editing and deletion
- Entry search and filtering
- Markdown rendering in TUI
- Additional storage backends
- API layer for remote access
- Entry linking/references
- Export/import functionality

## Key Design Decisions

1. **Strategy Pattern for Storage**: Makes it easy to swap storage backends
2. **Singleton State**: Ensures single source of truth
3. **Loose Coupling**: Layers communicate through well-defined interfaces
4. **TUI Observes State**: TUI renders state but doesn't modify it directly
5. **Controls Orchestrate**: Controls layer coordinates state and storage
6. **Pydantic Models**: Type-safe data with validation
7. **Textual for TUI**: Modern, async-capable TUI framework

## Common Issues and Solutions

### Issue: State not persisting
- Check `.zettelkasten/.state.json` exists and is writable
- Verify state initialization happens before operations

### Issue: Database locked
- Ensure only one process accesses a store at a time
- SQLite doesn't handle concurrent writes well

### Issue: TUI not updating
- Call `refresh_display()` after state changes
- Use screen callbacks to refresh parent screens

### Issue: Import errors
- Ensure package is installed: `pip install -e .`
- Check Python path includes project root

## Code Style

- Follow PEP 8
- Use type hints
- Docstrings for all public methods
- Black formatting (line length 100)
- MyPy for type checking

