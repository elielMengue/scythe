"""
    Textual application backing `scythe ui`.

    The TUI receives a pre-computed ScanResult (the CLI runs the scan
    with the same progress bar as `scythe scan`) and exposes a two-pane
    browse-and-select experience: projects on the left, the artifacts of
    the focused project on the right. Selection is tracked per artifact
    so the user can opt out of individual files within an otherwise
    cleanable project.
"""

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Input, Static

from scythe import __version__
from scythe.models.models import Project, ScanResult
from scythe.utils.utils import format_size


_FULL = "[x]"
_PARTIAL = "[~]"
_NONE = "[ ]"

_SORT_MODES = ["size", "date", "type", "path"]
_SORT_LABELS = {
    "size": "size ↓",
    "date": "newest",
    "type": "type",
    "path": "path",
}


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

    #filter-input {
        height: 3;
        margin: 0 2;
        display: none;
    }
    #filter-input.visible {
        display: block;
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
        Binding("s", "cycle_sort", "Sort"),
        Binding("slash", "show_filter", "Filter"),
        Binding("escape", "clear_filter", "Clear filter", show=False),
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
        self.filter_text: str = ""
        self.sort_mode: str = "size"

    # ------------------------------------------------------------------ compose

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self._status_text(), id="status")
        yield Input(
            placeholder="Filter projects (path or type) — Esc to close",
            id="filter-input",
        )
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

        atable = self.query_one("#artifacts-table", DataTable)
        atable.add_column("", key="mark", width=3)
        atable.add_column("Artifact", key="type")
        atable.add_column("Size", key="size", width=10)

        self._rebuild_projects_table()
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

    def _visible_projects(self) -> List[Project]:
        """Cleanable projects after applying the current filter and sort."""
        projects: Iterable[Project] = self.cleanable_projects
        needle = self.filter_text.lower().strip()
        if needle:
            projects = [
                p for p in projects
                if needle in str(p.path).lower()
                or needle in p.project_type.display_name.lower()
            ]
        return self._sort_projects(list(projects))

    def _sort_projects(self, projects: List[Project]) -> List[Project]:
        if self.sort_mode == "size":
            return sorted(projects, key=lambda p: p.total_artifact_size, reverse=True)
        if self.sort_mode == "date":
            def newest(p: Project):
                return max(
                    (a.last_modified for a in p.artifacts),
                    default=datetime.min,
                )
            return sorted(projects, key=newest, reverse=True)
        if self.sort_mode == "type":
            return sorted(projects, key=lambda p: p.project_type.display_name)
        if self.sort_mode == "path":
            return sorted(projects, key=lambda p: str(p.path))
        return projects

    def _rebuild_projects_table(self) -> None:
        if not self.cleanable_projects:
            # No tables exist in the empty layout; nothing to rebuild.
            return
        ptable = self.query_one("#projects-table", DataTable)
        ptable.clear()
        visible = self._visible_projects()
        for project in visible:
            self._add_project_row(ptable, project)
        atable = self.query_one("#artifacts-table", DataTable)
        if visible:
            self._refresh_artifacts_panel(visible[0])
        else:
            atable.clear()
        self._refresh_status()

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
        chips = [
            f"{len(self.cleanable_projects)} project(s)",
            f"{len(self.selected_artifacts)}/{total_artifacts} artifacts",
            f"{format_size(selected_size)} to free",
            f"sort: {_SORT_LABELS[self.sort_mode]}",
        ]
        if self.filter_text:
            chips.append(f"filter: '{self.filter_text}'")
        return (
            f"[bold cyan]scythe ui[/bold cyan]  [white]{self.scan_path}[/white]\n"
            f"[dim]{' · '.join(chips)}[/dim]"
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
        # A full rebuild keeps the displayed rows (which may be a
        # filtered subset) in sync without juggling per-row updates.
        self._rebuild_projects_table()

    def action_cycle_sort(self) -> None:
        idx = _SORT_MODES.index(self.sort_mode)
        self.sort_mode = _SORT_MODES[(idx + 1) % len(_SORT_MODES)]
        self._rebuild_projects_table()

    def action_show_filter(self) -> None:
        inp = self.query_one("#filter-input", Input)
        inp.add_class("visible")
        inp.focus()

    def action_clear_filter(self) -> None:
        inp = self.query_one("#filter-input", Input)
        inp.value = ""
        inp.remove_class("visible")
        self.filter_text = ""
        self._rebuild_projects_table()
        self.query_one("#projects-table", DataTable).focus()

    @on(Input.Changed, "#filter-input")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self.filter_text = event.value
        self._rebuild_projects_table()

    @on(Input.Submitted, "#filter-input")
    def _on_filter_submitted(self, event: Input.Submitted) -> None:
        # Enter applies the filter and returns focus to the project table
        # (the input stays visible so the user can see the active filter).
        self.query_one("#projects-table", DataTable).focus()


def run_tui(scan_path: Path, scan_result: Optional[ScanResult] = None) -> None:
    """Blocking entry point invoked by the `scythe ui` CLI subcommand."""
    ScytheApp(scan_path=scan_path, scan_result=scan_result).run()
