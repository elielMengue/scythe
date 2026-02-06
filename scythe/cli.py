"""
Command Line Interface - Implemented with Click-Rich
"""

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

import json
from datetime import datetime

from rich.table import Table

from scythe import __version__
from scythe.logger.logger import setup_logger
from scythe.scanner.scanner import scan_directory
from scythe.cleaner.cleaner import clean_artifacts
from scythe.ui.ui import (
    display_scan_result,
    progress_bar, interactive_select_project, confirm_action
)

from scythe.formatter.formatter import save_report


console = Console()

@click.group()
@click.version_option(version=__version__, prog_name="SCYTHE")
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Activate verbose mode',
)
@click.option(
    '--no-log-file',
    is_flag=True,
    help='Deactivate log mode',
)
@click.pass_context
def cli(ctx, verbose, no_log_file):
    """
        Scan directories for build artifacts and project metadata.

        Analyzes the file system to identify project roots (Node.js, Python, Rust, etc.)
         based on marker files and calculates the potential space reclaimable from
         their associated artifacts.

        \b
        Arguments:
            PATH    Directory to analyze (default: current directory)

        \b
        Options:
            --depth, -d        Maximum recursion depth (default: -1, infinite)
            --follow-symlinks  Follow symbolic links during traversal
            --verbose, -v      Show detailed logs and hidden project markers
            --no-log-file      Does not generate a log file

        \b
        Examples:
            scythe scan .                       # 1. Standard scan of current folder
            scythe scan ~/dev --depth 2         # 2. Shallow scan of your dev folder
            scythe scan /opt --follow-symlinks  # 3. Scan including symlinks
            scythe scan . --verbose             # 4. Scan with debug logging

        \b
        Notes:
            • Does not delete files; use the 'clean' command for removal
            • Scanning large directories (e.g., /) may require administrative privileges
            • Use --depth to speed up scanning on very large file systems
    """
    import logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger(name="scythe",level=log_level, log_file=not no_log_file)

    ctx.ensure_object(dict)
    ctx.obj["logger"] = logger
    ctx.obj["console"] = console

    if ctx.invoked_subcommand is None:
       display_header()

@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option(
    '--depth',
    '-d',
    type=int,
    default=-1,
    help="Depth of recursion",
    show_default=True,
)

@click.option(
    '--follow-symlinks',
    is_flag=True,
    help="Follow symbolics links"
)

@click.option(
    '--format',
    type=click.Choice(['table', 'tree', 'compact', 'json']),
    default='table',
    help='Format the output of the result'
)

@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Save the report of the result in a file'
)

@click.option('--no-artifacts', is_flag=True, help='Disable artifacts details output')

@click.pass_context
def scan(ctx, path, depth, follow_symlinks, format, output, no_artifacts):
    """
        Scan the directory
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]

    scan_path = Path(path).resolve()

    logger.info(f"Scanning directory: {path}")
    logger.info(f"Maximal Depth: {depth}")

    with progress_bar() as progress:
        task = progress.add_task("[cyan]Scanning...", total=None)

        def update_progress(message: str):
            progress.update(task, description=f"[cyan]{message}")

        # Lancer le scan
        result = scan_directory(
            path=scan_path,
            max_depth=depth,
            follow_symlinks=follow_symlinks,
            progress_callback=update_progress
        )


    if format == 'json':
        from scythe.formatter.formatter import format_to_json

        console.print(format_to_json(result))
    else:
        display_scan_result(
            result,
            scan_path,
            show_artifacts=not no_artifacts,
            format=format
        )

        # Save the report if needed
    if output:
        output_path = Path(output)
        output_format = 'json' if output_path.suffix == '.json' else 'csv'
        save_report(result, output_path, output_format)
        console.print(f"\n[green]✓ The report is saved: {output_path}[/green]")



@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.', metavar='[PATH]')
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help="Interactive mode, with manual selection",
)
@click.option(
    '--dry-run',
    is_flag=True,
    help="Dry run, without saving results",
)

@click.option(
    '--depth', '-d',
    type=int,
    default=-1,
    metavar='N',
    help="Maximal depth of scan",
    show_default=True
)

@click.option(
    '--force', '-f',
    is_flag=True,
    help="Force clean without confirmation"
)

@click.option(
    '--output', '-o',
    type=click.Path(),
    metavar='FILE',
    help='Save the report of the clean result in a file'
)

@click.pass_context
def clean(ctx, path, interactive, dry_run, depth, force, output):
    """
        Clean detected build artifacts.

        First scans the directory to identify projects with artifacts,
        then securely removes them after user confirmation.

        \b
        Arguments:
            PATH    Directory to clean (default: current directory)

        \b
        Operating Modes:
            --dry-run       Simulation mode (no actual deletion; recommended first)
            --interactive   Manually select which projects to clean
            --force         Skip confirmation (useful for automated scripts)

        \b
        Examples:
            scythe clean  path_to_project --dry-run              # 1. Preview what would be deleted
            scythe clean  path_to_project                        # 2. Clean with confirmation
            scythe clean  path_to_project  --interactive         # 3. Manual selection mode
            scythe clean  path_to_project  --force               # 4. Clean without confirmation
            scythe clean  path_to_project  -o report.json        # 5. Export results to a report

        \b
        Warning:
            • Deletion is PERMANENT (files are not moved to the trash)
            • Always perform a --dry-run first to avoid accidental data loss
            • Ensure that projects are not currently open or in use by other processes
    """
    global output_path
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]

    scan_path = Path(path).resolve()

    console.print("[bold cyan]Step 1/2 : Scanning projects...[/bold cyan]")

    with progress_bar() as progress:
        task = progress.add_task("[cyan]Scanning...", total=None)

        def update_progress(message: str) :
            progress.update(task, description=f"[cyan]{message}")

        scan_result = scan_directory(
            path=scan_path,
            max_depth=depth,
            progress_callback=update_progress
        )

    project_with_artifacts = [p for p in scan_result.projects if p.artifacts]

    if not project_with_artifacts :
        console.print(
            "\n[yellow]Nothing to clean[/yellow]"
        )
        return

    total_artifacts = sum(len(p.artifacts) for p in project_with_artifacts)
    total_size = sum(p.total_artifact_size for p in project_with_artifacts)
    from scythe.utils.utils import format_size

    console.print(
        f"\n[green]✓ Found {len(project_with_artifacts)} projects "
        f"with {total_artifacts} artifacts ({format_size(total_size)})[/green]"
    )

    if interactive :
        selected_projects = interactive_select_project
        (project_with_artifacts, scan_path)
        if not selected_projects :
            console.print(
                "[yellow]Nothing found[/yellow]"
            )
            return
    else :
        selected_projects = project_with_artifacts

    if not force and not dry_run :
        total_selected_size = sum(p.total_artifact_size for p in selected_projects)
        total_selected_artifacts = sum(len(p.artifacts) for p in selected_projects)

        if not confirm_action(
             "Confirm deletion ?",
            f"{total_selected_artifacts} artifacts - {format_size(total_selected_size)} will be deleted",
            default=False
        ) :
            console.print(
                "[yellow]Action canceled[/yellow]"
            )
            return

    console.print(
        "\n[bold cyan]Step 2/2 : Cleaning ...[/bold cyan]"
    )

    if dry_run :
        console.print("[yellow]DRY-RUN enabled - simulation, no data is deleted[/yellow]\n")

    with progress_bar() as progress:
        task = progress.add_task("[cyan]Cleaning...")
        total = len(selected_projects)

        def update_clean_progress(message: str) :
            progress.update(task, advance=1, description=f"[cyan]{message}")

        clean_result = clean_artifacts(
            selected_projects,
            dry_run=dry_run,
            progress_callback=update_clean_progress
        )


    console.print()
    if dry_run:
        console.print(
            f"[bold green]✓ [DRY-RUN] {clean_result.artifacts_deleted} artifacts "
            f"could be deleted ({clean_result.space_freed_formatted})[/bold green]"
        )

    else :
        console.print(
            f"[bold green]✓ Cleaning end in {clean_result.clean_duration:.2f}s[/bold green]"
        )

    console.print()

    result_table = Table(title="Cleaning results", box=box.ROUNDED)
    result_table.add_column("Metrics", style="cyan")
    result_table.add_column("Value", style="green", justify="right")

    result_table.add_row("Cleaned projects", str(len(clean_result.projects_cleaned)))
    result_table.add_row("Artifacts deleted", str(clean_result.artifacts_deleted))
    result_table.add_row("Freed memory", clean_result.space_freed_formatted)
    result_table.add_row("Operation success rate",  f"{clean_result.success_rate:.1f}%")

    if clean_result.skipped :
        result_table.add_row("Ignored",  f"[yellow]{len(clean_result.skipped)}[/yellow]")

    if clean_result.errors :
        result_table.add_row("Errors",  f"[red]{len(clean_result.errors)}[/red]")

    console.print(result_table)


    if clean_result.errors:
        console.print()
    console.print(f"[bold red] Errors : [/bold red]")
    for error in clean_result.errors[:5]:
        console.print(f"  [red]•[/red] {error}")

    if len(clean_result.errors) > 5:
        console.print(f"  [dim]... and {len(clean_result.errors) - 5} others[/dim]")

    report = {
        "clean_date": datetime.now().isoformat(),
        "path": str(scan_path),
        "summary": clean_result.get_summary(),
        "projects": [
            {
                "path": str(p.path),
                "type": p.project_type.value,
                "artifacts_deleted": len(p.artifacts)
            }
            for p in clean_result.projects_cleaned
        ],
        "errors": clean_result.errors,
        "skipped": clean_result.skipped
    }

    if output:
        output_path = Path(output)
        output_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        console.print(f"\n[green]✓ Report saved: {output_path}[/green]")


@cli.command()
@click.pass_context
def info(ctx):
    console = ctx.obj["console"]
    info_text = f"""
    [bold cyan]Scythe v{__version__}[/bold cyan]
    [italic white]A high-performance CLI utility to reclaim disk space by harvesting build artifacts.[/italic white]

    [bold underline]Supported Ecosystems & Patterns:[/bold underline]
    [yellow]• Node.js [/yellow]  : node_modules, dist, build, .next, .turbo, coverage
    [yellow]• Python  [/yellow]  : .venv, venv, __pycache__, .pytest_cache, .egg-info
    [yellow]• Rust    [/yellow]  : target/
    [yellow]• Java    [/yellow]  : target/ (Maven), build/, .gradle/ (Gradle)
    [yellow]• .NET    [/yellow]  : bin/, obj/

    [bold underline]Core Commands:[/bold underline]
    [bold green]scan[/bold green]   - Analyze directories to find projects and calculate potential savings.
    [bold green]clean[/bold green]  - Purge detected artifacts (supports [italic]--dry-run[/italic] and [italic]--interactive[/italic]).
    [bold green]info[/bold green]   - Display this overview and current configuration.

    [dim]Need more details? Run:[/dim] [bold reverse] scythe --help [/bold reverse]
    [dim]GitHub: https://github.com/elielMengue/scythe[/dim]
    """
    from scythe.banner.banner import VERSION, display_banner
    display_banner()
    console.print(Panel(info_text, title="Guide", border_style="cyan"))
def display_header():
    header = """
    [bold red] SCYTHE[/bold red]
    [yellow] Free your dir in few second [/yellow]
    """

    console.print(Panel(header, border_style="red"))

if "__main__" == __name__:
    cli()