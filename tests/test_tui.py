"""
    Smoke and interaction tests for the scythe ui TUI.

    Each test boots the app via Textual's `run_test()` Pilot in a
    headless event loop, drives a handful of keystrokes, and checks the
    resulting state. No real terminal is needed.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from scythe.models.models import (
    ArtifactInfo,
    Project,
    ProjectType,
    ScanResult,
)
from scythe.tui import ScytheApp


def _run(coro):
    asyncio.run(coro)


def _make_scan_result(root: Path) -> ScanResult:
    """Build a small ScanResult with two cleanable projects of different types."""
    p_node = Project(
        path=root / "web",
        project_type=ProjectType.NODE,
        marker_files=["package.json"],
        artifacts=[
            ArtifactInfo(
                path=root / "web" / "node_modules",
                size_bytes=200 * 1024 * 1024,
                last_modified=datetime.now(),
                artifact_type="node_modules",
            )
        ],
    )
    p_py = Project(
        path=root / "api",
        project_type=ProjectType.PYTHON,
        marker_files=["pyproject.toml"],
        artifacts=[
            ArtifactInfo(
                path=root / "api" / ".venv",
                size_bytes=80 * 1024 * 1024,
                last_modified=datetime.now(),
                artifact_type=".venv",
            )
        ],
    )
    return ScanResult(
        root_path=root,
        projects=[p_node, p_py],
        scan_duration=0.5,
        directories_scanned=42,
        files_scanned=420,
    )


def test_app_boots_and_quits(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            assert app.scan_path == tmp_path
            assert len(app.cleanable_projects) == 2
            await pilot.press("q")

    _run(go())


def test_empty_scan_renders_empty_panel(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=ScanResult(root_path=tmp_path))
        async with app.run_test() as pilot:
            # No cleanable projects → empty placeholder, no DataTable.
            assert app.cleanable_projects == []
            app.query_one("#empty")
            await pilot.press("q")

    _run(go())


def test_default_selection_is_everything(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            assert len(app.selected) == 2
            await pilot.press("q")

    _run(go())


def test_space_toggles_current_row(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # Cursor starts on row 0; space deselects it.
            await pilot.press("space")
            assert len(app.selected) == 1
            # Space again re-selects it.
            await pilot.press("space")
            assert len(app.selected) == 2
            await pilot.press("q")

    _run(go())


def test_toggle_all_clears_then_restores(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # Everything is selected by default; `a` clears all.
            await pilot.press("a")
            assert app.selected == set()
            # `a` again selects everything.
            await pilot.press("a")
            assert len(app.selected) == 2
            await pilot.press("q")

    _run(go())
