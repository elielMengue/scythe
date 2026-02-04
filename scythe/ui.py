"""
    USER INTERFACE INTERFACE
"""

from pathlib import Path
from typing import List, Optional, Set

from docutils.utils import relative_path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from scythe.models import ScanResult, ProjectType, Project
from scythe.logger import get_logger

console = Console()
logger = get_logger()


def display_scan_result(
        result: ScanResult,
        scan_path: Path,
        show_artifacts: bool = True,
        format: str = "table"
) -> None :
    """
        Format result of scan
    """

    console.print()
    console.print(f"[bold green]✓ Scand ends in {result.scan_duration:.2f}s[/bold green]")
    console.print()

    if result.total_projects == 0 :
        console.print("[yellow] No projects found. [/yellow]")
        return

    if format == "tree" :
        display_tree_view(result, scan_path)
    elif format == "compact" :
        display_compact_view(result, scan_path)
    else: display_table_view(result, scan_path)

    display_statistics(result)

    if show_artifacts and result.total_artifacts_size > 0:
        display_artifacts_detail(result)

def display_table_view(result: ScanResult, scan_path: Path) -> None:
    table = Table(title="Detected Projects", box=box.ROUNDED)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Path", style="white")
    table.add_column("Artifacts", style="yellow", justify="right")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Last Modified", style="dim", no_wrap=True)

    for project in result.projects :
        try:
            relative_path = project.path.relative_to(scan_path)
        except ValueError :
            relative_path = project.path

        artifact_count = len(project.artifacts)
        artifact_display = f"{artifact_count}" if artifact_count  > 0 else "[dim]0[/dim]"

        size_display = project.total_size_formatted if project.total_artifact_size > 0 else "[dim]0[/dim]"

        last_modified = "N/A"

        if project.artifacts :
            most_recent = max(project.artifacts, key=lambda a: a.last_modified)
            days_ago = (result.scan_date - most_recent.last_modified).days

            if days_ago == 0 :
                last_modified = "Today"
            elif days_ago == 1 :
                last_modified = "Yesterday"
            elif days_ago < 7 :
                last_modified = f"{days_ago} days ago"
            elif days_ago < 30 :
                last_modified = f"{days_ago // 7} weeks ago"
            else :
                last_modified = f"{days_ago // 30} months ago"

        table.add_row(
            project.project_type.display_name,
            str(relative_path),
            artifact_display,
            size_display,
            last_modified
        )
    console.print(table)



