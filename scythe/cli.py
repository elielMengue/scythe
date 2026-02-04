"""
Command Line Interface - Implemented with Click-Rich
"""
from email.policy import default

import click
from docutils.utils import relative_path
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from pathlib import Path

from scythe import __version__
from scythe.logger import setup_logger, get_logger
from scythe.scanner import scan_directory
from scythe.ui import (
    display_scan_result,
    interactive_select_project,
    confirm_action,
    progress_bar
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
    type=click.choice(['table', 'tree', 'compact', 'json']),
    default='table',
    help='Format the output of the result'
)

@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Save the report of the result in a file'
)

@click.option('--no-artifacts', is_flag=True, help='Disable artifacts details output')
)
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
@click.pass_context
def clean(ctx, path, interactive, dry_run):
    """
        Clean the directory
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]

    logger.info(f"Cleaning directory: {path}")

    if dry_run :
        console.print("[cyan] DRY_RUN MODE active [/cyan]")

    if interactive:
        console.print("[cyan] INTERACTIVE MODE active [/cyan]")

    #TODO: Implemente this feature

    console.print("[yellow] Feature Not Implemented [/yellow]")

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