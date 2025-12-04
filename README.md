# Zettelkasten CLI

A command-line tool for managing your Zettelkasten notes with a beautiful TUI interface.

## Version

Current version: **0.1.0**

## Installation

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd my-zk
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

### Production Build

To create a standalone executable using PyInstaller:

```bash
pyinstaller --onefile --name zk --console zettelkasten/cli.py
```

The executable will be in the `dist/` directory.

## Quick Start

1. **Initialize Zettelkasten** in your current directory:
```bash
zk init
```

This creates a `.zettelkasten/` directory in your current working directory.

2. **Create or switch to a store**:
```bash
zk store list          # List all stores
zk store switch <name> # Switch to a store
```

3. **Create an entry** (opens TUI):
```bash
zk entry create
```

4. **View all entries** (debug mode):
```bash
zk debug-view
```

5. **Launch full TUI**:
```bash
zk tui
```

## Commands

### Initialization

- `zk init` - Initialize zettelkasten in the current directory
  - Creates `.zettelkasten/` directory
  - Prompts for creating an initial store

### Store Management

- `zk store list` - List all available stores
- `zk store switch <name>` - Switch to a different store
- `zk store delete <name>` - Delete a store (with confirmation)

### Entry Management

- `zk entry create` - Create a new entry (opens TUI editor)
- `zk debug-view` - Display all entries in the current store

### TUI

- `zk tui` - Launch the full TUI interface

## TUI Keyboard Shortcuts

### Main Screen
- `s` - Show stores
- `c` - Create entry
- `d` - Debug view
- `q` - Quit

### Store Selection Screen
- `n` - New store
- `Esc` - Cancel/Close
- Use arrow keys to navigate, Enter to select

### Entry Editor
- `Ctrl+S` - Save entry
- `Esc` - Cancel

## Project Structure

```
my-zk/
├── zettelkasten/          # Main package
│   ├── cli.py            # CLI entry point
│   ├── state.py          # Application state (singleton)
│   ├── controls.py       # Controls layer (user interactions)
│   ├── storage/          # Storage layer (strategy pattern)
│   │   ├── base.py       # Abstract storage interface
│   │   └── sqlite_storage.py  # SQLite implementation
│   ├── models/           # Data models (Pydantic)
│   │   ├── store.py
│   │   └── entry.py
│   └── tui/              # TUI layer (Textual)
│       ├── app.py
│       └── screens/      # TUI screens
├── tests/                # Test files
├── requirements.txt      # Production dependencies
├── requirements-dev.txt # Development dependencies
└── setup.py             # Package setup
```

## Architecture

The application follows a layered architecture with loose coupling:

1. **Storage Layer** - Abstract interface for data persistence (strategy pattern)
2. **Models Layer** - Pydantic models for data validation
3. **State Layer** - Singleton application state (single source of truth)
4. **Controls Layer** - Handles user interactions and orchestrates operations
5. **TUI Layer** - Textual-based user interface (renders state, doesn't modify it)

## Storage

Currently, only SQLite storage is supported. The storage layer uses a strategy pattern, making it easy to add other storage backends in the future.

Database files are stored in `.zettelkasten/{store_name}.db`. Each store has its own database file.

## Data Model

### Store
- `id` - Unique identifier
- `name` - Store name (unique)
- `format` - Storage format (currently "sqlite")
- `created_at` - Creation timestamp

### Entry
- `id` - Unique identifier
- `store_id` - Reference to store
- `message` - Entry content (markdown supported but not rendered)
- `tags` - List of tags (array of strings)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black zettelkasten/
```

### Type Checking

```bash
mypy zettelkasten/
```

## Troubleshooting

### "Zettelkasten not initialized"

Run `zk init` in your current directory first.

### "No store selected"

Use `zk store switch <name>` to select a store, or create one through the TUI.

### Database locked errors

Make sure you're not accessing the same store from multiple processes simultaneously.

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]

