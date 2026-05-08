"""
Command Line Interface - Implemented with Click-Rich
"""
import os
import click
import csv
import json
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scythe import __version__
from scythe.logger.logger import setup_logger
from scythe.models.models import ProjectType
from scythe.scanner.scanner import scan_directory
from scythe.cleaner.cleaner import clean_artifacts
from scythe.ui.ui import (
    display_scan_result,
    display_run_header,
    display_clean_plan,
    display_clean_footer,
    progress_bar,
    scan_progress,
    clean_progress,
    interactive_select_project,
    confirm_action,
)
from scythe.formatter.formatter import save_report
from scythe.utils.utils import format_size, parse_size_threshold


def _parse_only_filter(value):
    """Parse a comma-separated --only value into a set of ProjectType."""
    if not value:
        return None
    types = set()
    for token in value.split(','):
        token = token.strip()
        if not token:
            continue
        try:
            types.add(ProjectType.from_alias(token))
        except ValueError as exc:
            raise click.BadParameter(str(exc), param_hint='--only')
    return types or None


def _parse_min_size(value):
    """Parse a human-readable --min-size value into bytes."""
    if value is None:
        return None
    try:
        return parse_size_threshold(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint='--min-size')




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
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress decorative output (progress bars, panels, headers). Keeps summary lines and --output writes.',
)
@click.option(
    '--no-color',
    is_flag=True,
    help='Disable ANSI colored output.',
)
@click.pass_context
def cli(ctx, verbose, no_log_file, quiet, no_color):
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
    logger = setup_logger(name="scythe", level=log_level, log_file=not no_log_file)

    ctx.ensure_object(dict)
    
    env_no_color = os.environ.get("NO_COLOR") not in (None, "")
    disable_color = no_color or env_no_color

    console = Console(no_color=disable_color)
    ctx.obj["logger"] = logger
    ctx.obj["console"] = console
    ctx.obj["quiet"] = quiet

    if ctx.invoked_subcommand is None and not quiet:
        display_header(console)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option(
    '--depth', '-d',
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
@click.option(
    '--only',
    type=str,
    default=None,
    metavar='TYPES',
    help='Comma-separated list of project types to keep (e.g. node,python,rust)'
)
@click.option(
    '--older-than',
    type=int,
    default=0,
    metavar='DAYS',
    help='Only keep artifacts whose last_modified is older than DAYS days'
)
@click.option(
    '--min-size',
    type=str,
    default=None,
    metavar='SIZE',
    help='Only keep artifacts at or above SIZE (e.g. 100MB, 1GB, 512KB)'
)
@click.pass_context
def scan(ctx, path, depth, follow_symlinks, format, output, no_artifacts, only, older_than, min_size):
    """
        Scan the directory
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]
    quiet = ctx.obj.get("quiet", False)

    scan_path = Path(path).resolve()
    only_types = _parse_only_filter(only)
    min_size_bytes = _parse_min_size(min_size)

    logger.info(f"Scanning directory: {path}")
    logger.info(f"Maximal Depth: {depth}")

    if format != 'json' and not quiet:
        display_run_header(
            command="scan",
            path=scan_path,
            filters={
                "depth": depth if depth >= 0 else None,
                "follow-symlinks": "yes" if follow_symlinks else None,
                "only": ", ".join(t.display_name for t in only_types) if only_types else None,
                "older-than": f"{older_than}d" if older_than and older_than > 0 else None,
                "min-size": format_size(min_size_bytes) if min_size_bytes else None,
            },
        )

    if quiet:
        result = scan_directory(
            path=scan_path,
            max_depth=depth,
            follow_symlinks=follow_symlinks,
            progress_callback=None,
        )
    else:
        with scan_progress() as progress:
            task = progress.add_task("[cyan]Scanning...", total=None)
            counter = {"dirs": 0}

            def update_progress(message: str):
                counter["dirs"] += 1
                current = message.removeprefix("Scanning ").strip()
                tail = current[-50:] if len(current) > 50 else current
                progress.update(
                    task,
                    description=(
                        f"[cyan]Scanning[/cyan] "
                        f"[bold]{counter['dirs']}[/bold] [dim]dirs[/dim] "
                        f"[dim]· {tail}[/dim]"
                    ),
                )

            result = scan_directory(
                path=scan_path,
                max_depth=depth,
                follow_symlinks=follow_symlinks,
                progress_callback=update_progress,
            )

    if only_types:
        before = len(result.projects)
        result.projects = [p for p in result.projects if p.project_type in only_types]
        logger.info(
            f"--only filter: kept {len(result.projects)}/{before} projects "
            f"({', '.join(t.display_name for t in only_types)})"
        )

    if older_than and older_than > 0:
        from scythe.utils.utils import filter_projects_by_artifact_age
        before = len(result.projects)
        result.projects = filter_projects_by_artifact_age(result.projects, older_than)
        logger.info(
            f"--older-than {older_than} filter: kept {len(result.projects)}/{before} projects"
        )

    if min_size_bytes:
        from scythe.utils.utils import filter_projects_by_artifact_size
        before_projects = len(result.projects)
        before_artifacts = sum(len(project.artifacts) for project in result.projects)
        result.projects = filter_projects_by_artifact_size(result.projects, min_size_bytes)
        after_artifacts = sum(len(project.artifacts) for project in result.projects)
        logger.info(
            f"--min-size {format_size(min_size_bytes)} filter: kept "
            f"{after_artifacts}/{before_artifacts} artifacts across "
            f"{len(result.projects)}/{before_projects} projects"
        )

    if format == 'json':
        from scythe.formatter.formatter import format_to_json
        console.print(format_to_json(result))
    elif not quiet:
        display_scan_result(
            result,
            scan_path,
            show_artifacts=not no_artifacts,
            format=format
        )

    if output:
        output_path = Path(output)
        output_format = 'json' if output_path.suffix == '.json' else 'csv'
        save_report(result, output_path, output_format)
        if not quiet:
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
@click.option(
    '--only',
    type=str,
    default=None,
    metavar='TYPES',
    help='Comma-separated list of project types to clean (e.g. node,python,rust)'
)
@click.option(
    '--older-than',
    type=int,
    default=0,
    metavar='DAYS',
    help='Only clean artifacts whose last_modified is older than DAYS days'
)
@click.option(
    '--min-size',
    type=str,
    default=None,
    metavar='SIZE',
    help='Only clean artifacts at or above SIZE (e.g. 100MB, 1GB, 512KB)'
)
@click.option(
    '--trash',
    is_flag=True,
    help='Move artifacts to scythe\'s recoverable trash instead of deleting them. Use `scythe restore` to undo.'
)
@click.option(
    '--follow-symlinks',
    is_flag=True,
    help="Follow symbolic links during scan"
)
@click.pass_context
def clean(ctx, path, interactive, dry_run, depth, force, output, only, older_than, min_size, trash, follow_symlinks):
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
            --trash         Move artifacts to scythe's recoverable trash
                            (undo with `scythe restore`)

        \b
        Examples:
            scythe clean  path_to_project --dry-run              # 1. Preview what would be deleted
            scythe clean  path_to_project                        # 2. Clean with confirmation (PERMANENT)
            scythe clean  path_to_project  --trash               # 3. Recoverable cleanup
            scythe clean  path_to_project  --interactive         # 4. Manual selection mode
            scythe clean  path_to_project  --force               # 5. Clean without confirmation
            scythe clean  path_to_project  -o report.json        # 6. Export results to a report

        \b
        Warning:
            • Without --trash, deletion is PERMANENT (files are NOT sent to the OS bin)
            • Always perform a --dry-run first when in doubt
            • Ensure that projects are not currently open or in use by other processes
    """
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]
    quiet = ctx.obj.get("quiet", False)

    scan_path = Path(path).resolve()
    only_types = _parse_only_filter(only)
    min_size_bytes = _parse_min_size(min_size)

    mode_chip = "dry-run" if dry_run else ("trash" if trash else "permanent")
    if not quiet:
        display_run_header(
            command="clean",
            path=scan_path,
            filters={
                "mode": mode_chip,
                "depth": depth if depth >= 0 else None,
                "follow-symlinks": "yes" if follow_symlinks else None,
                "only": ", ".join(t.display_name for t in only_types) if only_types else None,
                "older-than": f"{older_than}d" if older_than and older_than > 0 else None,
                "min-size": format_size(min_size_bytes) if min_size_bytes else None,
                "interactive": "yes" if interactive else None,
            },
        )

    if quiet:
        scan_result = scan_directory(
            path=scan_path,
            max_depth=depth,
            follow_symlinks=follow_symlinks,
            progress_callback=None,
        )
    else:
        with scan_progress() as progress:
            task = progress.add_task("[cyan]Scanning...", total=None)
            counter = {"dirs": 0}

            def update_progress(message: str):
                counter["dirs"] += 1
                current = message.removeprefix("Scanning ").strip()
                tail = current[-50:] if len(current) > 50 else current
                progress.update(
                    task,
                    description=(
                        f"[cyan]Scanning[/cyan] "
                        f"[bold]{counter['dirs']}[/bold] [dim]dirs[/dim] "
                        f"[dim]· {tail}[/dim]"
                    ),
                )

            scan_result = scan_directory(
                path=scan_path,
                max_depth=depth,
                follow_symlinks=follow_symlinks,
                progress_callback=update_progress,
            )

    project_with_artifacts = [p for p in scan_result.projects if p.artifacts]

    if only_types:
        before = len(project_with_artifacts)
        project_with_artifacts = [p for p in project_with_artifacts if p.project_type in only_types]
        logger.info(
            f"--only filter: kept {len(project_with_artifacts)}/{before} projects "
            f"({', '.join(t.display_name for t in only_types)})"
        )

    if older_than and older_than > 0:
        from scythe.utils.utils import filter_projects_by_artifact_age
        before = len(project_with_artifacts)
        project_with_artifacts = filter_projects_by_artifact_age(
            project_with_artifacts, older_than
        )
        logger.info(
            f"--older-than {older_than} filter: kept "
            f"{len(project_with_artifacts)}/{before} projects"
        )

    if min_size_bytes:
        from scythe.utils.utils import filter_projects_by_artifact_size
        before_projects = len(project_with_artifacts)
        before_artifacts = sum(len(project.artifacts) for project in project_with_artifacts)
        project_with_artifacts = filter_projects_by_artifact_size(
            project_with_artifacts, min_size_bytes
        )
        after_artifacts = sum(len(project.artifacts) for project in project_with_artifacts)
        logger.info(
            f"--min-size {format_size(min_size_bytes)} filter: kept "
            f"{after_artifacts}/{before_artifacts} artifacts across "
            f"{len(project_with_artifacts)}/{before_projects} projects"
        )

    if not project_with_artifacts :
        if not quiet:
            console.print(
                "\n[yellow]Nothing to clean.[/yellow]"
            )
        return

    total_artifacts = sum(len(p.artifacts) for p in project_with_artifacts)
    total_size = sum(p.total_artifact_size for p in project_with_artifacts)

    if not quiet:
        display_clean_plan(
            project_with_artifacts,
            total_size_formatted=format_size(total_size),
            total_artifacts=total_artifacts,
            trash=trash,
            dry_run=dry_run,
        )

    if interactive:
        selected_projects = interactive_select_project(project_with_artifacts, scan_path)
        if not selected_projects :
            if not quiet:
                console.print(
                    "[yellow]Nothing selected.[/yellow]"
                )
            return
    else:
        selected_projects = project_with_artifacts

    if not force and not dry_run:
        total_selected_size = sum(p.total_artifact_size for p in selected_projects)
        total_selected_artifacts = sum(len(p.artifacts) for p in selected_projects)

        if not confirm_action(
            "Confirm deletion?",
            f"{total_selected_artifacts} artifacts ({format_size(total_selected_size)}) will be deleted",
            default=False
        ) :
            if not quiet:
                console.print(
                    "[yellow]Action canceled.[/yellow]"
                )
            return

    trash_mover = None
    manifest_path = None
    if trash and not dry_run:
        from scythe.trash import TrashMover
        trash_mover = TrashMover()
        logger.info(
            f"Trash mode active — artifacts will be moved under {trash_mover.trash_dir}"
        )

    total = len(selected_projects)
    if quiet:
        clean_result = clean_artifacts(
            selected_projects,
            dry_run=dry_run,
            progress_callback=None,
            trash_mover=trash_mover,
        )
    else:
        with clean_progress() as progress:
            task = progress.add_task("[cyan]Cleaning...", total=total)

            def update_clean_progress(message: str):
                current = message.removeprefix("Cleaning ").strip()
                tail = current[-40:] if len(current) > 40 else current
                progress.update(
                    task,
                    advance=1,
                    description=(
                        f"[cyan]Cleaning[/cyan] "
                        f"[dim]· {tail}[/dim]"
                    ),
                )

            clean_result = clean_artifacts(
                selected_projects,
                dry_run=dry_run,
                progress_callback=update_clean_progress,
                trash_mover=trash_mover,
            )

    if trash_mover is not None:
        manifest_path = trash_mover.finalize(scan_path=scan_path)

    if not quiet:
        display_clean_footer(
            artifacts_deleted=clean_result.artifacts_deleted,
            artifacts_total=total_artifacts,
            space_freed_formatted=clean_result.space_freed_formatted,
            duration=clean_result.clean_duration,
            dry_run=dry_run,
            trashed=trash_mover is not None,
            skipped=len(clean_result.skipped),
            errors=len(clean_result.errors),
        )

        if trash_mover is not None:
            console.print(
                f"[dim]Run id: [bold]{trash_mover.run_id}[/bold] · "
                f"undo with [bold]scythe restore[/bold][/dim]"
            )

        if clean_result.errors:
            console.print()
            console.print("[bold red]Errors:[/bold red]")
            for error in clean_result.errors[:5]:
                console.print(f"  [red]•[/red] {error}")
            if len(clean_result.errors) > 5:
                console.print(f"  [dim]... and {len(clean_result.errors) - 5} more[/dim]")

    report = {
        "clean_date": datetime.now().isoformat(),
        "path": str(scan_path),
        "summary": clean_result.get_summary(),
        "projects": [
            {
                "path": str(p.path),
                "type": p.project_type.value,
                "artifacts_deleted": len(p.artifacts),
                "space_freed_bytes": p.total_artifact_size,
                "space_freed": p.total_size_formatted,
            }
            for p in clean_result.projects_cleaned
        ],
        "errors": clean_result.errors,
        "skipped": clean_result.skipped
    }

    if output:
        output_path = Path(output)
        if output_path.suffix == ".csv":
            write_clean_csv(report, output_path)
        else:
            write_clean_json(report, output_path)
        if not quiet:
            console.print(f"\n[green]✓ Report saved: {output_path}[/green]")


@cli.command()
@click.argument('run_id', required=False, default=None, metavar='[RUN_ID]')
@click.option(
    '--list', 'list_only',
    is_flag=True,
    help='List recoverable runs and exit, without restoring anything.'
)
@click.pass_context
def restore(ctx, run_id, list_only):
    """
        Restore a previous `clean --trash` run.

        Without arguments, restores the most recent run. Pass a RUN_ID
        (visible in the output of the original clean, or via
        `scythe restore --list`) to target a specific run.

        \b
        Examples:
            scythe restore --list                # show available runs
            scythe restore                       # undo the most recent --trash run
            scythe restore 20260502-153000-123456  # undo a specific run

        \b
        Notes:
            • Only runs created with `scythe clean --trash` are recoverable.
            • An item is skipped (not failed) when its destination path
              already exists or its trash payload has been removed.
    """
    console = ctx.obj["console"]
    logger = ctx.obj["logger"]

    from scythe.trash import list_runs, load_manifest, restore_run
    from scythe.utils.utils import format_size

    runs = list_runs()

    if list_only:
        if not runs:
            console.print("[yellow]No recoverable runs found.[/yellow]")
            return

        table = Table(title="Recoverable runs", box=box.ROUNDED)
        table.add_column("Run ID", style="cyan")
        table.add_column("Date", style="white")
        table.add_column("Items", justify="right")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Restored?", justify="center")

        for manifest_path in runs:
            data = load_manifest(manifest_path)
            items = data.get("items", [])
            total = sum(item.get("size_bytes", 0) for item in items)
            restored = "[green]✓[/green]" if data.get("restored_at") else "[dim]—[/dim]"
            table.add_row(
                data["run_id"],
                data.get("started_at", "?"),
                str(len(items)),
                format_size(total),
                restored,
            )
        console.print(table)
        return

    if not runs:
        console.print(
            "[yellow]No recoverable runs found.[/yellow] "
            "Did you run [bold]scythe clean --trash[/bold]?"
        )
        return

    if run_id:
        manifest_path = next(
            (p for p in runs if p.stem == run_id),
            None,
        )
        if manifest_path is None:
            console.print(f"[red]No run with id [bold]{run_id}[/bold] found.[/red]")
            console.print("[dim]List available runs with [bold]scythe restore --list[/bold].[/dim]")
            ctx.exit(1)
    else:
        manifest_path = runs[0]

    data = load_manifest(manifest_path)
    if data.get("restored_at"):
        console.print(
            f"[yellow]Run [bold]{data['run_id']}[/bold] was already restored "
            f"on {data['restored_at']}.[/yellow]"
        )
        return

    items = data.get("items", [])
    total = sum(item.get("size_bytes", 0) for item in items)
    console.print(
        f"\n[bold cyan]Restoring run {data['run_id']}[/bold cyan] — "
        f"{len(items)} items ({format_size(total)})"
    )
    if data.get("scan_path"):
        console.print(f"[dim]original scan path: {data['scan_path']}[/dim]")

    summary = restore_run(manifest_path)

    result_table = Table(title="Restore results", box=box.ROUNDED)
    result_table.add_column("Metric", style="cyan")
    result_table.add_column("Value", justify="right", style="green")
    result_table.add_row("Restored", str(len(summary["restored"])))
    if summary["skipped"]:
        result_table.add_row("Skipped", f"[yellow]{len(summary['skipped'])}[/yellow]")
    if summary["errors"]:
        result_table.add_row("Errors", f"[red]{len(summary['errors'])}[/red]")
    console.print(result_table)

    if summary["skipped"]:
        console.print("\n[bold yellow]Skipped:[/bold yellow]")
        for entry in summary["skipped"][:10]:
            console.print(f"  [yellow]•[/yellow] {entry['path']} — {entry['reason']}")
        if len(summary["skipped"]) > 10:
            console.print(f"  [dim]... and {len(summary['skipped']) - 10} more[/dim]")

    if summary["errors"]:
        console.print("\n[bold red]Errors:[/bold red]")
        for entry in summary["errors"][:10]:
            console.print(f"  [red]•[/red] {entry['path']} — {entry['error']}")
        ctx.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.', metavar='[PATH]')
@click.option('--depth', '-d', type=int, default=-1, metavar='N', show_default=True,
              help='Maximal depth of scan')
@click.option('--follow-symlinks', is_flag=True, help='Follow symbolic links during scan')
@click.option('--only', type=str, default=None, metavar='TYPES',
              help='Comma-separated project types to keep (e.g. node,python,rust)')
@click.option('--older-than', type=int, default=0, metavar='DAYS',
              help='Only keep artifacts whose last_modified is older than DAYS days')
@click.option('--min-size', type=str, default=None, metavar='SIZE',
              help='Only keep artifacts at or above SIZE (e.g. 100MB, 1GB, 512KB)')
@click.option('--no-trash', is_flag=True,
              help='Delete artifacts directly instead of moving them to scythe trash.')
@click.pass_context
def ui(ctx, path, depth, follow_symlinks, only, older_than, min_size, no_trash):
    """
        Launch the interactive TUI for browsing and cleaning artifacts.

        Full-screen alternative to `scan`/`clean` for exploration: filter,
        sort, toggle items, and trigger a recoverable clean — all without
        leaving the terminal.

        \b
        Arguments:
            PATH    Directory to scan (default: current directory)

        \b
        Examples:
            scythe ui                                # current directory
            scythe ui ~/projects --min-size 100MB    # focus on big artifacts
            scythe ui . --only node,python -d 3      # narrow scan

        \b
        Notes:
            • The TUI scans up-front and caches the result in memory.
            • Cleanups triggered from the TUI default to --trash; undo
              with the in-app shortcut or `scythe restore` from the CLI.
              Pass --no-trash to delete directly instead.
    """
    from scythe.tui import run_tui

    logger = ctx.obj["logger"]
    scan_path = Path(path).resolve()
    only_types = _parse_only_filter(only)
    min_size_bytes = _parse_min_size(min_size)

    logger.info(f"Launching TUI for: {scan_path}")

    run_tui(
        scan_path=scan_path,
        scan_options={
            "depth": depth,
            "follow_symlinks": follow_symlinks,
            "only_types": only_types,
            "older_than": older_than,
            "min_size_bytes": min_size_bytes,
        },
        use_trash=not no_trash,
    )


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
    [bold green]scan[/bold green]    - Analyze directories to find projects and calculate potential savings.
    [bold green]clean[/bold green]   - Purge detected artifacts (supports [italic]--dry-run[/italic], [italic]--interactive[/italic], [italic]--trash[/italic]).
    [bold green]restore[/bold green] - Undo a previous [italic]clean --trash[/italic] run.
    [bold green]info[/bold green]    - Display this overview and current configuration.

    [dim]Need more details? Run:[/dim] [bold reverse] scythe --help [/bold reverse]
    [dim]GitHub: https://github.com/elielMengue/scythe[/dim]
    """
    from scythe.banner.banner import VERSION, display_banner
    display_banner()
    console.print(Panel(info_text, title="Guide", border_style="cyan"))


def display_header(console):
    header = """
    [bold red]SCYTHE[/bold red]
    [yellow]Reclaim disk space in seconds.[/yellow]
    """
    console.print(Panel(header, border_style="red"))


_CLEAN_CSV_HEADERS = [
    "path",
    "type",
    "artifacts_deleted",
    "space_freed_bytes",
    "space_freed",
]


def write_clean_json(report, output_path):
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_clean_csv(report, output_path):
    projects = report.get("projects", [])
    headers = list(projects[0].keys()) if projects else _CLEAN_CSV_HEADERS
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(projects)


if __name__ == "__main__":
    cli()
