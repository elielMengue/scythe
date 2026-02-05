"""
    USER INTERFACE INTERFACE
"""
from email.policy import default
from pathlib import Path
from typing import List, Optional, Set
from collections import defaultdict

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

    """if show_artifacts and result.total_artifacts_size > 0:
        display_artifacts_detail(result)"""

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


def display_tree_view(result: ScanResult, scan_path: Path) -> None:
    tree = Tree(
        f"[bold cyan]{scan_path.name}[/bold cyan]",
        guide_style="dim"
    )

    project_by_type = defaultdict(list)

    for project in result.projects :
        ptype = project.project_type
        if ptype in project_by_type :
            project_by_type[ptype] = []
        project_by_type[ptype].append(project)

    for project_type, projects in project_by_type.items() :
        type_branch = tree.add(
            f"[cyan]{project_type.display_name}[/cyan] ({len(projects)} projects) projects"
        )

        for project in projects :
            try:
                relative_path = project.path.relative_to(scan_path)
            except ValueError :
                relative_path = project.path

            project_info = f"[white]{relative_path}[/white]"

            if project.artifacts :
                project_info += f" [yellow]({len(project.artifacts)} artifacts, {project.total_artifact_size})[/yellow]"
            project_branch = type_branch.add(project_info)

            for artifact in project.artifacts[:5] :
                project_branch.add(
                    f"[dim] {artifact.artifact_type}[/dim] [green]{artifact.size_formatted}"
                )

            if len(project.artifacts) > 5 :
                project_branch.add(f"[dim] ... and {len(project.artifacts) - 5} more artifacts [/dim]")

    console.print(tree)


def display_compact_view(result: ScanResult, scan_path: Path) -> None:
    console.print("[bold cyan] Project detected : [/bold cyan]")
    console.print()

    for i, project in enumerate(result.projects, 1) :
        try:
            relative_path = project.path.relative_to(scan_path)

        except ValueError :
            relative_path = project.path

        artifact_info = ""

        if project.artifacts :
            artifact_info = f" • [yellow]{len(project.artifacts)} artifact(s)[/yellow] • [green]{project.total_size_formatted}[/green]"

        console.print(
            f"{i:2d}. [cyan]{project.project_type.display_name:12}[/cyan] "
            f"[white]{relative_path}[/white]"
            f"{artifact_info}"
        )


def display_statistics(result: ScanResult) -> None:
    console.print()
    stats_table = Table(title="Statistics", box=box.SIMPLE)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Directories Scanned", str(result.directories_scanned))
    stats_table.add_row("Files scanned", str(result.files_scanned))
    stats_table.add_row("Projects detected", str(result.total_projects))
    stats_table.add_row("Artifacts found", str(sum(p.artifact_count for p in result.projects)))
    stats_table.add_row("Total size", result.total_artifact_size_formatted)

    if result.errors :
        stats_table.add_row("Errors", f"[red]{len(result.errors)}[/red]")

    console.print(stats_table)


"""def display_artifacts_detail(result: ScanResult) -> None:
    console.print()
    console.print(f"[bold cyan]Artifacts found:[/bold cyan]")

    for project in result.projects :
        if project.artifacts :
            console.print(f"[bold white]{project.path.name}[/bold white] ({project.project_type.display_name}: ")
            for artifact in project.artifacts :
                console.print(
                    f"  [yellow]•[/yellow] {artifact.artifact_type:<20} "
                    f"[green]{artifact.size_formatted:>10}[/green]"
                )
"""
def display_errors(errors: List[str], max_display: int = 5 ) -> None:
    console.print()
    console.print("[bold red] Errors that occurs : [/bold red]")

    for error in errors :
        console.print(f"  [red]•[/red] {error}")

    if len(errors) > max_display:
        console.print(f" [dim] ... and {len(errors) -max_display} others [/dim]")


def interactive_select_project(
        projects: List[Project],
        scan_path: Path,
) -> List[Project] :
    """
        Interactive mode to select project to clean
        return: a List of projects
    """

    if not projects :
        console.print("[yellow] Nothing to select [/yellow]")
        return []

    console.print()
    console.print("[bold cyan] Interactive mode - Select project [/bold cyan]")
    console.print("[dim] Enter project number id or select all [/dim]")

    #selection table
    table = Table(box=box.SIMPLE)
    table.add_column("№", style="cyan", justify="right")
    table.add_column("Type", style="cyan")
    table.add_column("Chemin", style="white")
    table.add_column("Artefacts", style="yellow", justify="right")
    table.add_column("Taille", style="green", justify="right")

    for i, project in enumerate(projects, 1) :
        try:
            relative_path = project.path.relative_to(scan_path)

        except ValueError :
            relative_path = project.path

        table.add_row(
            str(i),
            project.project_type.display_name,
            str(relative_path),
            str(len(project.artifacts)),
            project.total_size_formatted
        )

    console.print(table)
    console.print()

    #Ask for selection

    while True :
        selection = Prompt.ask(
            "[bold cyan] Selection [/bold cyan]",
            default="all"
        )

        try:
            selected_indices = parse_selection(selection, len(projects))
            selected_projects = [projects[i] for i in selected_indices]

            total_size = sum(p.total_artifact_size for p in selected_projects)
            from scythe.utils import format_size

            console.print()
            console.print(
                f"[yellow]→ {len(selected_projects)} selected projects "
                f"({format_size(total_size)} to free)[/yellow]"
            )

            return selected_projects
        except ValueError as e :
            console.print(f"[red]invalid selection: {e}[/red]")
            continue


def parse_selection(selection: str, max_index: int)  -> List[int]:
    selection = selection.strip().lower()

    if selection == "all" :
        return list(range(max_index))

    indices = set()

    for part in selection.split(',') :
        part = part.strip()

        if '-' in part :
            start, end = part.split('-', 1)
            start_idx = int(start.strip()) - 1
            end_idx = int(end.strip()) - 1

            if start_idx < 0 or end_idx >= max_index or start_idx > end_idx:
                raise ValueError(f"Invalid range: {part}")

            indices.update(range(start_idx, end_idx + 1))

        else :
            idx = int(part) - 1
            if idx < 0 or idx >= max_index:
                raise ValueError(f"Out of index: {part}")
            indices.add(idx)

    return sorted(list(indices))


def confirm_action(
        action: str,
        details: str = "",
        default: bool = True
)-> bool:

    """
        Confirm an action before the action
    """

    console.print()
    console.print()
    if details:
        console.print(f"[yellow]{details}[/yellow]")

    return Confirm.ask(
        f"[bold cyan]{action}[/bold cyan]",
        default=default
    )


def display_summary_panel(
        title: str,
        content: str,
        style: str = "cyan"
)-> None:
    console.print()
    console.print(
        Panel(
            content,
            title=f"[bold]{title}[/bold]",
            border_style=style,
            padding=(1, 2)
        )
    )


def progress_bar(description: str = "Processing ...") -> Progress:

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )
