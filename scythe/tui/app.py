"""
    Textual application backing `scythe ui`.

    The TUI receives a pre-computed ScanResult (the CLI runs the scan
    with the same progress bar as `scythe scan`) and lets the user
    browse the projects, toggle selection, and — in later commits —
    drill into artifacts and trigger a recoverable clean.
"""

from pathlib import Path
from typing import Optional, Set

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, Static

from scythe import __version__
from scythe.models.models import ScanResult
from scythe.utils.utils import format_size


_SELECTED_MARK = "[x]"
_UNSELECTED_MARK = "[ ]"


class ScytheApp(App):
    """Interactive TUI for browsing and cleaning project artifacts."""

    CSS = """
    #status {
        dock: top;
        height: 3;
        padding: 1 2;
        background: $boost;
        border-bottom: solid $primary;
    }

    #table {
        height: 1fr;
    }

    #empty {
        align: center middle;
        height: 1fr;
        padding: 4;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_selection", "Toggle"),
        Binding("a", "toggle_all", "Toggle all"),
    ]

    TITLE = "scythe"
    SUB_TITLE = f"v{__version__}"

    def __init__(
            self,
            scan_path: Path,
            scan_result: Optional[ScanResult] = None,
    ) -> None:
        super().__init__()
        self.scan_path = scan_path
        self.scan_result = scan_result or ScanResult(root_path=scan_path)
        self.cleanable_projects = [
            p for p in self.scan_result.projects if p.artifacts
        ]
        # Selection defaults to "everything cleanable" — the TUI is opt-out.
        self.selected: Set[Path] = {p.path for p in self.cleanable_projects}

    # ------------------------------------------------------------------ compose

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self._status_text(), id="status")
        if self.cleanable_projects:
            yield DataTable(id="table", cursor_type="row", zebra_stripes=True)
        else:
            yield Static(
                "No cleanable projects under this path.\n"
                "[dim]Press [bold]q[/bold] to quit.[/dim]",
                id="empty",
            )
        yield Footer()

    def on_mount(self) -> None:
        if not self.cleanable_projects:
            return
        table = self.query_one("#table", DataTable)
        table.add_column("", key="mark", width=3)
        table.add_column("Type", key="type", width=14)
        table.add_column("Path", key="path")
        table.add_column("Artifacts", key="artifacts", width=10)
        table.add_column("Size", key="size", width=12)
        for project in self.cleanable_projects:
            self._add_row(table, project)
        table.focus()

    # ------------------------------------------------------------------ helpers

    def _add_row(self, table: DataTable, project) -> None:
        try:
            rel = project.path.relative_to(self.scan_path)
        except ValueError:
            rel = project.path
        mark = _SELECTED_MARK if project.path in self.selected else _UNSELECTED_MARK
        table.add_row(
            mark,
            project.project_type.display_name,
            str(rel),
            str(project.artifact_count),
            project.total_size_formatted,
            key=str(project.path),
        )

    def _status_text(self) -> str:
        total = len(self.cleanable_projects)
        selected = len(self.selected)
        size = sum(
            p.total_artifact_size
            for p in self.cleanable_projects
            if p.path in self.selected
        )
        return (
            f"[bold cyan]scythe ui[/bold cyan]  [white]{self.scan_path}[/white]\n"
            f"[dim]{total} project(s) · {selected} selected · "
            f"{format_size(size)} to free[/dim]"
        )

    def _refresh_status(self) -> None:
        self.query_one("#status", Static).update(self._status_text())

    def _project_at_cursor(self):
        if not self.cleanable_projects:
            return None
        table = self.query_one("#table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        return next(
            (p for p in self.cleanable_projects if str(p.path) == row_key.value),
            None,
        )

    # ------------------------------------------------------------------ actions

    def action_toggle_selection(self) -> None:
        project = self._project_at_cursor()
        if project is None:
            return
        if project.path in self.selected:
            self.selected.remove(project.path)
        else:
            self.selected.add(project.path)
        table = self.query_one("#table", DataTable)
        mark = _SELECTED_MARK if project.path in self.selected else _UNSELECTED_MARK
        table.update_cell(str(project.path), "mark", mark)
        self._refresh_status()

    def action_toggle_all(self) -> None:
        if not self.cleanable_projects:
            return
        if len(self.selected) == len(self.cleanable_projects):
            self.selected.clear()
        else:
            self.selected = {p.path for p in self.cleanable_projects}
        table = self.query_one("#table", DataTable)
        for project in self.cleanable_projects:
            mark = _SELECTED_MARK if project.path in self.selected else _UNSELECTED_MARK
            table.update_cell(str(project.path), "mark", mark)
        self._refresh_status()


def run_tui(scan_path: Path, scan_result: Optional[ScanResult] = None) -> None:
    """Blocking entry point invoked by the `scythe ui` CLI subcommand."""
    ScytheApp(scan_path=scan_path, scan_result=scan_result).run()
