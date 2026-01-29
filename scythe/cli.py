"""
Command Line Interface - Implemented with Click-Rich
"""
import os
import click
from rich.console import Console
from rich.panel import Panel

from scythe import __version__
from scythe.logger import setup_logger, get_logger

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
    logger = setup_logger(level=log_level, log_file=not no_log_file)

    ctx.ensure_object(dict)
    ctx.obj["logger"] = logger
    ctx.obj["console"] = console

    if ctx.invoked_subcommand is None:
       display_header()

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.getcwd())
@click.option(
    '--depth',
    '-d',
    type=int,
    default=-1,
    help="Depth of recursion",
    show_default=True,
)
@click.pass_context
def scan(ctx, path, depth):
    """
        Scan the directory
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]

    logger.info(f"Scanning directory: {path}")
    logger.info(f"Maximal Depth: {depth}")

    #TODO: Implement the feature

    console.print("[yellow] Feature Not Implemented [/yellow]")

@cli.command()
@click.argument('path', type=click.Path(exists=True), default=os.getcwd())
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