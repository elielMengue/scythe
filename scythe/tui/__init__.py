"""
    Interactive TUI for browsing and cleaning project artifacts.

    Public surface: ScytheApp (the Textual app class) and run_tui (the
    blocking entry point used by the `scythe ui` CLI subcommand). Textual
    is a heavy import; the rest of scythe does not depend on this
    package, so importing it stays opt-in via the `ui` subcommand.
"""

from scythe.tui.app import ScytheApp, run_tui

__all__ = ["ScytheApp", "run_tui"]
