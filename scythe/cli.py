"""
Command Line Interface - Implemented with Click-Rich
"""
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
@click.pass_context
def scan(ctx, path, depth, follow_symblinks):
    """
        Scan the directory
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]

    scan_path = Path(path).resolve()

    logger.info(f"Scanning directory: {path}")
    logger.info(f"Maximal Depth: {depth}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.desciption]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress :
        task = progress.add_task("[cyan]Scanning ...", total=None)

        def update_progress(message: str):
            progress.update(task, description=f"[cyan]{message}")

        result = scan_directory(
            path=scan_path,
            max_depth=depth,
            follow_symlinks=follow_symblinks,
            progress_callback=update_progress()
        )

    console.print()

    console.print(f"[bold green]✓ Scan end in {result.scan_duration:.2f}s[/bold green]")

        #Result format

    table = Table(title="Detected Project", box=box.ROUNDED)
    table.add_column('Type', style="cyan", no_wrap=True)
    table.add_column("Path", style="white")
    table.add_column("Markers", style="yellow")

    if result.total_projects == 0:
        console.print("[yellow]No project found[/yellow]")
    else:
        for project in result.projects:
            try:
                relative_path = project.path.relative_to(scan_path)
            except ValueError:
                relative_path = project.path

            table.add_row(
                project.project_types.display_name,
                str(relative_path),
                ", ".join(project.marker_files[:3])
            )

        console.print(table)

    #Stats

    console.print()
    stats_table = Table(title="Statistics", box=box.SIMPLE)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Repositories scanned", str(result.directories_scanned))
    stats_table.add_row("Files scanned", str(result.files_scanned))
    stats_table.add_row("Detected project", str(result.total_projects))

    if result.errors :
        console.print()
        console.print("[bold red] Unable, orrors occures [/bold red]")
        for error in result.errors[:5] :
            console.print(f"[red]•[/red] {error}")
        if len(result.errors)  > 5:
            console.print(f" [dim]... and {len(result.errors) - 5} other orrors[/dim]")




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