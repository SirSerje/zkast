"""CLI entry point for Zettelkasten."""
from typing import Tuple
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from zettelkasten.state import AppState
from zettelkasten.storage import SQLiteStorage
from zettelkasten.controls import Controls
from zettelkasten.tui.app import ZettelkastenApp

console = Console()


def get_zk_path() -> Path:
    """Get the zettelkasten directory path."""
    return Path.cwd() / ".zettelkasten"


def ensure_initialized() -> Tuple[AppState, Controls]:
    """
    Ensure zettelkasten is initialized and return state/controls.

    Returns:
        Tuple of (AppState, Controls)

    Raises:
        click.ClickException: If not initialized
    """
    zk_path = get_zk_path()
    if not zk_path.exists():
        raise click.ClickException(
            "Zettelkasten not initialized. Run 'zk init' first."
        )

    state = AppState()
    storage = SQLiteStorage(zk_path)
    state.initialize(zk_path, storage)

    controls = Controls(state, storage)

    return state, controls


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Zettelkasten CLI - A tool for managing your notes."""
    pass


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["sqlite"], case_sensitive=False),
    default="sqlite",
    help="Storage format (currently only sqlite available)",
)
def init(format: str):
    """Initialize zettelkasten in the current directory."""
    zk_path = get_zk_path()

    if zk_path.exists():
        if click.confirm(
            "Zettelkasten already initialized. Re-initialize? (This won't delete data)"
        ):
            console.print(f"Re-initializing zettelkasten at {zk_path}")
        else:
            console.print("Initialization cancelled.")
            return

    zk_path.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Zettelkasten initialized at {zk_path}")

    # Initialize storage
    storage = SQLiteStorage(zk_path)
    state = AppState()
    state.initialize(zk_path, storage)

    # Prompt for creating initial store
    if click.confirm("Would you like to create an initial store?"):
        store_name = click.prompt("Enter store name", default="default")
        try:
            store = storage.create_store(store_name, format)
            state.set_current_store(store)
            console.print(f"[green]✓[/green] Created store: {store_name}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")


@cli.group()
def store():
    """Manage stores."""
    pass


@store.command("list")
def store_list():
    """List all available stores."""
    try:
        state, controls = ensure_initialized()
        stores = controls.list_stores()

        if not stores:
            console.print("No stores found.")
            return

        table = Table(title="Available Stores")
        table.add_column("Name", style="cyan")
        table.add_column("Format", style="magenta")
        table.add_column("Created", style="green")

        current_store_name = (
            state.current_store.name if state.current_store else None
        )

        for store in stores:
            marker = "* " if store.name == current_store_name else "  "
            table.add_row(
                f"{marker}{store.name}",
                store.format,
                str(store.created_at) if store.created_at else "N/A",
            )

        console.print(table)
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")


@store.command("switch")
@click.argument("name")
def store_switch(name: str):
    """Switch to a different store."""
    try:
        state, controls = ensure_initialized()
        if controls.switch_store(name):
            console.print(f"[green]✓[/green] Switched to store: {name}")
        else:
            console.print(f"[red]Error:[/red] Store '{name}' not found.")
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")


@store.command("delete")
@click.argument("name")
@click.option("--force", is_flag=True, help="Skip confirmation")
def store_delete(name: str, force: bool):
    """Delete a store."""
    try:
        state, controls = ensure_initialized()

        if state.current_store and state.current_store.name == name:
            console.print(
                "[red]Error:[/red] Cannot delete current store. Switch to another store first."
            )
            return

        if not force:
            if not click.confirm(f"Are you sure you want to delete store '{name}'?"):
                console.print("Deletion cancelled.")
                return

        if controls.delete_store(name):
            console.print(f"[green]✓[/green] Deleted store: {name}")
        else:
            console.print(f"[red]Error:[/red] Store '{name}' not found.")
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")


@cli.group()
def entry():
    """Manage entries."""
    pass


@entry.command("create")
@click.argument("text")
@click.argument("tags", required=False, default="")
def entry_create(text: str, tags: str):
    """Create a new entry.

    TEXT: The entry message/content
    TAGS: Comma-separated tags (optional)
    """
    try:
        state, controls = ensure_initialized()

        if not state.current_store:
            console.print(
                "[red]Error:[/red] No store selected. Use 'zk store switch <name>' first."
            )
            return

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

        # Create entry
        entry = controls.create_entry(text, tag_list)
        console.print(f"[green]✓[/green] Entry created with ID: {entry.id}")
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@cli.command("create")
@click.argument("text")
@click.argument("tags", required=False, default="")
def create(text: str, tags: str):
    """Create a new entry (shortcut command).

    TEXT: The entry message/content
    TAGS: Comma-separated tags (optional)
    """
    try:
        state, controls = ensure_initialized()

        if not state.current_store:
            console.print(
                "[red]Error:[/red] No store selected. Use 'zk store switch <name>' first."
            )
            return

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []

        # Create entry
        entry = controls.create_entry(text, tag_list)
        console.print(f"[green]✓[/green] Entry created with ID: {entry.id}")
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@cli.command("debug-view")
def debug_view():
    """Display all entries in the current store (debug mode)."""
    try:
        state, controls = ensure_initialized()

        if not state.current_store:
            console.print(
                "[red]Error:[/red] No store selected. Use 'zk store switch <name>' first."
            )
            return

        entries = controls.list_entries()

        if not entries:
            console.print("No entries found.")
            return

        console.print(f"\n[bold]Debug View - Store: {state.current_store.name}[/bold]")
        console.print(f"Total entries: {len(entries)}\n")
        console.print("=" * 80)

        for entry in entries:
            console.print(f"\n[cyan]Entry ID:[/cyan] {entry.id}")
            console.print(f"[green]Created:[/green] {entry.created_at}")
            console.print(f"[green]Updated:[/green] {entry.updated_at}")
            console.print(
                f"[yellow]Tags:[/yellow] {', '.join(entry.tags) if entry.tags else 'None'}"
            )
            console.print(f"[bold]Message:[/bold]\n{entry.message}")
            console.print("=" * 80)

    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@cli.command("tui")
def tui():
    """Launch the TUI interface."""
    try:
        state, controls = ensure_initialized()
        app = ZettelkastenApp()
        app.run()
    except click.ClickException as e:
        console.print(f"[red]Error:[/red] {e.message}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
