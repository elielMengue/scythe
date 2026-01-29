"""
Command Line Interface - Implemented with Click-Rich
"""

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

def display_header():
    header = """
    [bold red] SCYTHE[/bold red]
    [yellow] Free your dir in few second [/yellow]
    """

    console.print(Panel(header, border_style="red"))

if "__main__" == __name__:
    cli()