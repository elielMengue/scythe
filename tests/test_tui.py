"""
    Smoke and interaction tests for the scythe ui TUI.

    Each test boots the app via Textual's `run_test()` Pilot in a
    headless event loop, drives a handful of keystrokes, and checks the
    resulting state.
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
    """A small ScanResult with two cleanable projects, one of which has 2 artifacts."""
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
            ),
            ArtifactInfo(
                path=root / "web" / "dist",
                size_bytes=20 * 1024 * 1024,
                last_modified=datetime.now(),
                artifact_type="dist",
            ),
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
            assert app.cleanable_projects == []
            app.query_one("#empty")
            await pilot.press("q")

    _run(go())


def test_default_selection_is_everything(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # 2 + 1 = 3 artifacts total.
            assert len(app.selected_artifacts) == 3
            await pilot.press("q")

    _run(go())


def test_space_on_project_deselects_all_its_artifacts(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # Cursor is on the first project (web, with 2 artifacts).
            await pilot.press("space")
            # Both web artifacts dropped, only the api one remains.
            assert len(app.selected_artifacts) == 1
            await pilot.press("space")
            assert len(app.selected_artifacts) == 3
            await pilot.press("q")

    _run(go())


def test_space_on_artifact_toggles_just_that_artifact(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # Switch focus to the artifacts pane.
            await pilot.press("tab")
            await pilot.press("space")
            # One artifact deselected → 2 remaining.
            assert len(app.selected_artifacts) == 2
            # The web project is now in 'partial' state.
            web = next(p for p in app.cleanable_projects if p.path.name == "web")
            assert app._project_selection_state(web) == "partial"
            await pilot.press("q")

    _run(go())


def test_toggle_all_clears_then_restores(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            await pilot.press("a")
            assert app.selected_artifacts == set()
            await pilot.press("a")
            assert len(app.selected_artifacts) == 3
            await pilot.press("q")

    _run(go())


def test_sort_cycles_through_modes(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            assert app.sort_mode == "size"
            await pilot.press("s")
            assert app.sort_mode == "date"
            await pilot.press("s")
            assert app.sort_mode == "type"
            await pilot.press("s")
            assert app.sort_mode == "path"
            await pilot.press("s")
            assert app.sort_mode == "size"
            await pilot.press("q")

    _run(go())


def test_sort_size_orders_largest_project_first(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            visible = app._visible_projects()
            # The web project (200 + 20 MB) is larger than api (80 MB).
            assert visible[0].path.name == "web"
            assert visible[1].path.name == "api"
            await pilot.press("q")

    _run(go())


def test_filter_input_narrows_visible_projects(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path, scan_result=_make_scan_result(tmp_path))
        async with app.run_test() as pilot:
            # Programmatic filter — bypasses the keyboard so the test
            # doesn't depend on Input keyboard handling.
            app.filter_text = "api"
            app._rebuild_projects_table()
            visible = app._visible_projects()
            assert len(visible) == 1
            assert visible[0].path.name == "api"
            # Clear via the action.
            app.action_clear_filter()
            assert app.filter_text == ""
            assert len(app._visible_projects()) == 2
            await pilot.press("q")

    _run(go())
