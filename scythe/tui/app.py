"""
    Textual application backing `scythe ui`.

    For now the app only boots, prints a welcome line with the resolved
    scan path, and quits on `q`. Subsequent commits add the project list,
    the artifact tree, filters/sort, and the clean action.
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from scythe import __version__


class ScytheApp(App):
    """Interactive TUI for browsing and cleaning project artifacts."""

    CSS = """
    #welcome {
        align: center middle;
        height: 1fr;
        padding: 2 4;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    TITLE = "scythe"
    SUB_TITLE = f"v{__version__}"

    def __init__(self, scan_path: Path) -> None:
        super().__init__()
        self.scan_path = scan_path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(
            f"[bold cyan]scythe ui[/bold cyan]\n"
            f"[white]{self.scan_path}[/white]\n\n"
            f"[dim]Press [bold]q[/bold] to quit.[/dim]",
            id="welcome",
        )
        yield Footer()


def run_tui(scan_path: Path) -> None:
    """Blocking entry point invoked by the `scythe ui` CLI subcommand."""
    ScytheApp(scan_path=scan_path).run()
