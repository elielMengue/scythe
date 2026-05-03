"""
    Textual application backing `scythe ui`.

    The TUI receives a pre-computed ScanResult (the CLI runs the scan
    with the same progress bar as `scythe scan`) and exposes a two-pane
    browse-and-select experience: projects on the left, the artifacts of
    the focused project on the right. Selection is tracked per artifact
    so the user can opt out of individual files within an otherwise
    cleanable project.
"""

from pathlib import Path
from typing import Optional, Set

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from scythe import __version__
from scythe.models.models import Project, ScanResult
from scythe.utils.utils import format_size


_FULL = "[x]"
_PARTIAL = "[~]"
_NONE = "[ ]"


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

    #panes {
        height: 1fr;
    }

    #projects-table {
        width: 60%;
    }

    #artifacts-table {
        width: 40%;
        border-left: solid $primary;
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
        Binding("space", "toggle", "Toggle"),
        Binding("a", "toggle_all", "Toggle all"),
        Binding("tab", "focus_next", "Focus pane", show=False),
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
        # Selection is opt-out: every artifact starts selected.
        self.selected_artifacts: Set[Path] = {
            a.path for p in self.cleanable_projects for a in p.artifacts
        }

    # ------------------------------------------------------------------ compose

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self._status_text(), id="status")
        if self.cleanable_projects:
            with Horizontal(id="panes"):
                yield DataTable(
                    id="projects-table", cursor_type="row", zebra_stripes=True,
                )
                yield DataTable(
                    id="artifacts-table", cursor_type="row", zebra_stripes=True,
                )
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
        ptable = self.query_one("#projects-table", DataTable)
        ptable.add_column("", key="mark", width=3)
        ptable.add_column("Type", key="type", width=12)
        ptable.add_column("Path", key="path")
        ptable.add_column("Size", key="size", width=10)
        for project in self.cleanable_projects:
            self._add_project_row(ptable, project)

        atable = self.query_one("#artifacts-table", DataTable)
        atable.add_column("", key="mark", width=3)
        atable.add_column("Artifact", key="type")
        atable.add_column("Size", key="size", width=10)
        self._refresh_artifacts_panel(self.cleanable_projects[0])

        ptable.focus()

    # ------------------------------------------------------------------ events

    @on(DataTable.RowHighlighted, "#projects-table")
    def _on_project_highlighted(self, event: DataTable.RowHighlighted) -> None:
        project = self._project_for_key(event.row_key.value)
        if project is not None:
            self._refresh_artifacts_panel(project)

    # ------------------------------------------------------------------ helpers

    def _project_for_key(self, key) -> Optional[Project]:
        return next(
            (p for p in self.cleanable_projects if str(p.path) == key),
            None,
        )

    def _project_selection_state(self, project: Project) -> str:
        selected = sum(
            1 for a in project.artifacts if a.path in self.selected_artifacts
        )
        if selected == 0:
            return "none"
        if selected == len(project.artifacts):
            return "all"
        return "partial"

    def _project_marker(self, project: Project) -> str:
        return {
            "all": _FULL,
            "partial": _PARTIAL,
            "none": _NONE,
        }[self._project_selection_state(project)]

    def _add_project_row(self, table: DataTable, project: Project) -> None:
        try:
            rel = project.path.relative_to(self.scan_path)
        except ValueError:
            rel = project.path
        table.add_row(
            self._project_marker(project),
            project.project_type.display_name,
            str(rel),
            project.total_size_formatted,
            key=str(project.path),
        )

    def _refresh_artifacts_panel(self, project: Project) -> None:
        atable = self.query_one("#artifacts-table", DataTable)
        atable.clear()
        for artifact in project.artifacts:
            mark = _FULL if artifact.path in self.selected_artifacts else _NONE
            atable.add_row(
                mark,
                artifact.artifact_type,
                artifact.size_formatted,
                key=str(artifact.path),
            )

    def _status_text(self) -> str:
        total_artifacts = sum(len(p.artifacts) for p in self.cleanable_projects)
        selected_size = sum(
            a.size_bytes
            for p in self.cleanable_projects
            for a in p.artifacts
            if a.path in self.selected_artifacts
        )
        return (
            f"[bold cyan]scythe ui[/bold cyan]  [white]{self.scan_path}[/white]\n"
            f"[dim]{len(self.cleanable_projects)} project(s) · "
            f"{len(self.selected_artifacts)}/{total_artifacts} artifacts · "
            f"{format_size(selected_size)} to free[/dim]"
        )

    def _refresh_status(self) -> None:
        self.query_one("#status", Static).update(self._status_text())

    def _current_project(self) -> Optional[Project]:
        ptable = self.query_one("#projects-table", DataTable)
        if ptable.row_count == 0:
            return None
        row_key, _ = ptable.coordinate_to_cell_key(ptable.cursor_coordinate)
        return self._project_for_key(row_key.value)

    def _current_artifact(self):
        project = self._current_project()
        if project is None:
            return None
        atable = self.query_one("#artifacts-table", DataTable)
        if atable.row_count == 0:
            return None
        row_key, _ = atable.coordinate_to_cell_key(atable.cursor_coordinate)
        return next(
            (a for a in project.artifacts if str(a.path) == row_key.value),
            None,
        )

    # ------------------------------------------------------------------ actions

    def action_toggle(self) -> None:
        """`space` toggles a project (full select/deselect) or an artifact."""
        focused = self.focused
        if focused is None:
            return
        if focused.id == "projects-table":
            self._toggle_current_project()
        elif focused.id == "artifacts-table":
            self._toggle_current_artifact()

    def _toggle_current_project(self) -> None:
        project = self._current_project()
        if project is None:
            return
        if self._project_selection_state(project) == "all":
            for a in project.artifacts:
                self.selected_artifacts.discard(a.path)
        else:
            for a in project.artifacts:
                self.selected_artifacts.add(a.path)
        ptable = self.query_one("#projects-table", DataTable)
        ptable.update_cell(str(project.path), "mark", self._project_marker(project))
        self._refresh_artifacts_panel(project)
        self._refresh_status()

    def _toggle_current_artifact(self) -> None:
        project = self._current_project()
        artifact = self._current_artifact()
        if project is None or artifact is None:
            return
        if artifact.path in self.selected_artifacts:
            self.selected_artifacts.discard(artifact.path)
        else:
            self.selected_artifacts.add(artifact.path)
        atable = self.query_one("#artifacts-table", DataTable)
        mark = _FULL if artifact.path in self.selected_artifacts else _NONE
        atable.update_cell(str(artifact.path), "mark", mark)
        ptable = self.query_one("#projects-table", DataTable)
        ptable.update_cell(str(project.path), "mark", self._project_marker(project))
        self._refresh_status()

    def action_toggle_all(self) -> None:
        if not self.cleanable_projects:
            return
        all_paths = {
            a.path for p in self.cleanable_projects for a in p.artifacts
        }
        if self.selected_artifacts == all_paths:
            self.selected_artifacts.clear()
        else:
            self.selected_artifacts = all_paths
        ptable = self.query_one("#projects-table", DataTable)
        for project in self.cleanable_projects:
            ptable.update_cell(
                str(project.path), "mark", self._project_marker(project),
            )
        current = self._current_project()
        if current is not None:
            self._refresh_artifacts_panel(current)
        self._refresh_status()


def run_tui(scan_path: Path, scan_result: Optional[ScanResult] = None) -> None:
    """Blocking entry point invoked by the `scythe ui` CLI subcommand."""
    ScytheApp(scan_path=scan_path, scan_result=scan_result).run()
