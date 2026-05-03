"""
    Smoke tests for the scythe ui TUI.

    Each test boots the app via Textual's `run_test()` Pilot, drives a
    handful of keystrokes, and checks the resulting state. The Pilot
    runs the app in a headless event loop so no real terminal is
    required.
"""

import asyncio
from pathlib import Path

from scythe.tui import ScytheApp


def _run(coro):
    """Run an async coroutine inside a fresh event loop."""
    asyncio.run(coro)


def test_app_boots_and_quits(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path)
        async with app.run_test() as pilot:
            assert app.scan_path == tmp_path
            # The welcome widget must be mounted after compose.
            app.query_one("#welcome")
            await pilot.press("q")

    _run(go())


def test_app_q_binding_quits(tmp_path: Path):
    async def go():
        app = ScytheApp(scan_path=tmp_path)
        async with app.run_test() as pilot:
            await pilot.press("q")
            # After quit, _exit is set; the context manager will return.

    _run(go())
