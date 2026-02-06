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
@click.argument('path', type=click.Path(exists=True), default='.')
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
    help="Maximal depth of scan"
)

@click.option(
    '--force', '-f',
    is_flag=True,
    help="Force clean without confirmation"
)

@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Save the report of the clean result in a file'
)

@click.pass_context
def clean(ctx, path, interactive, dry_run, depth, force, output):
    """
        Clean the directory
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
        [bold cyan]Artifact-Scythe v{__version__}[/bold cyan]
    
    [yellow]Un outil CLI pour nettoyer les artefacts de build[/yellow]
    
    [bold]Types de projets supportés:[/bold]
    • Node.js (node_modules, dist, build)
    • Python (.venv, __pycache__, .pytest_cache)
    • Rust (target/)
    • Java/Maven/Gradle (target/, build/)
    
    [bold]Commandes disponibles:[/bold]
    • scan   - Scanner un répertoire
    • clean  - Nettoyer les artefacts
    • info   - Afficher ces informations
    
    [dim]Pour plus d'aide: scythe --help[/dim]
    """

    console.print(Panel(info_text, title="Guide", border_style="cyan"))
def display_header():
    header = """
    [bold red] SCYTHE[/bold red]
    [yellow] Free your dir in few second [/yellow]
    """

    console.print(Panel(header, border_style="red"))

if "__main__" == __name__:
    cli()