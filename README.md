# Artifact-Scythe

> Reclaim disk space by harvesting the build artifacts you forgot about.

[![CI](https://github.com/elielMengue/scythe/actions/workflows/ci.yml/badge.svg)](https://github.com/elielMengue/scythe/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/artifact-scythe.svg)](https://pypi.org/project/artifact-scythe/)
[![Python versions](https://img.shields.io/pypi/pyversions/artifact-scythe.svg)](https://pypi.org/project/artifact-scythe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


![Demo](demo/demo.gif)

[MP4 version](demo/demo.mp4)

`scythe` is a Python CLI that walks your projects directory, identifies each
project's ecosystem (Node, Python, Rust, Java, Go, Ruby, .NET) from its
marker files, and locates the bulky build artifacts that ecosystem leaves
behind — `node_modules`, `.venv`, `__pycache__`, `target/`, `build/`, and
the rest. It reports how much space each one is wasting and, when you tell
it to, deletes them.

It is safe by default: every `clean` previews what is about to happen and
asks for confirmation, and a `--dry-run` mode lets you check the plan
before running for real.

## Why

A laptop used daily for a year typically holds 30–80 GB of stale
`node_modules`, abandoned virtualenvs, cached compiler output, and CI
scratch directories. None of it is load-bearing — but finding and removing
it by hand across dozens of project folders is tedious and error-prone.
`scythe` does it in two commands.

## How does this compare to `npkill` / `kondo` / `cleanpy`?

Existing tools cover one ecosystem each, well. `scythe` covers a
mixed-stack `~/projects` folder in one workflow.

| Tool       | Ecosystems covered                                | UX                | Filters                              | Reports         | Distribution                |
|------------|---------------------------------------------------|-------------------|--------------------------------------|-----------------|-----------------------------|
| `npkill`   | Node only (`node_modules`)                        | Interactive TUI   | Sort by size / age                   | None            | npm                         |
| `kondo`    | Rust + a handful (Node, JS, Java, Haskell, …)     | Interactive prompt| Older-than                           | None            | Cargo, Homebrew             |
| `cleanpy`  | Python only                                       | CLI               | Cache types                          | None            | pip                         |
| **`scythe`** | **Node, Python, Rust, Java (Maven + Gradle), Go, Ruby, .NET** (Swift planned) | **CLI + interactive TUI** (`scythe ui`) | `--only`, `--older-than`, `--min-size` (`--ignore` planned) | **JSON / CSV** export, dry-run report, **recoverable trash + `scythe restore`** | **pipx**, pip, **Docker** (multi-arch), standalones planned |

When to reach for which:
- Only have a `node_modules` problem? `npkill` is purpose-built.
- Mostly Rust? `kondo` is great.
- Mixed-stack folder, want filters / reports / scripting / CI integration,
  or you also need to clean Python virtualenvs and Java build dirs in the
  same pass? That's where `scythe` is meant to live.

## Quick start

```bash
pipx install artifact-scythe          # one-line global install

scythe scan ~/projects                # see what's eating your disk
scythe clean ~/projects --dry-run     # preview the deletions
scythe clean ~/projects               # do it (with confirmation)
```

## Install

### With `pipx` (recommended)

[`pipx`](https://pipx.pypa.io/) installs `scythe` into its own isolated
virtual environment and exposes the `scythe` command globally on your
`PATH`. It's the right tool for Python CLIs: no clash with your project
deps, no `sudo`, one command to upgrade.

```bash
pipx install artifact-scythe          # install
pipx upgrade artifact-scythe          # update later
pipx uninstall artifact-scythe        # remove cleanly
```

Don't have `pipx` yet? `python -m pip install --user pipx && python -m pipx ensurepath`
(restart your shell once).

### With `pip`

If you don't want the isolated install, plain `pip` works too:

```bash
pip install --user artifact-scythe    # user-level install
```

### Naming note

The PyPI distribution is `artifact-scythe` (the `scythe` slot on PyPI was
taken), but the installed command and the Python module are both `scythe`.
Scripts written against `scythe ...` keep working unchanged.

### With Docker

If you'd rather not install anything locally (CI agents, throwaway VMs,
or just trying it out), the official image is published on GHCR for both
`linux/amd64` and `linux/arm64`:

```bash
# scan the current directory
docker run --rm -v "$PWD":/work ghcr.io/elielmengue/scythe:latest scan /work

# clean with a dry-run
docker run --rm -v "$PWD":/work ghcr.io/elielmengue/scythe:latest \
    clean /work --dry-run
```

Tags follow the PyPI release: `:latest`, `:0.7.0`, `:0.7`, `:0`. The
rolling `:edge` tag tracks `main`.

### From source

```bash
git clone https://github.com/elielMengue/scythe.git
cd scythe
pip install -e ".[dev]"
```

## Usage

`scythe` is a Click group with five subcommands — `scan`, `clean`,
`restore`, `ui`, `info` — plus a small set of options that apply to
every invocation.

### Global options

These work with any subcommand and must be passed *before* the
subcommand name (e.g. `scythe --verbose scan .`).

| Option           | Description                                                                                |
|------------------|--------------------------------------------------------------------------------------------|
| `--verbose, -v`  | Enable DEBUG-level logging (per-directory walks, filter decisions, internal state).         |
| `--no-log-file`  | Skip writing the timestamped log file under `./logs/`. Console output is unaffected.        |
| `--version`      | Print the installed version and exit.                                                       |
| `--help`         | Show the top-level help and exit. Available on every subcommand too (`scythe scan --help`). |

By default each run drops a `logs/scythe_YYYYMMDD_HHMMSS.log` file in
the current working directory. Use `--no-log-file` for one-off runs in
sandboxes or CI where you don't want the side effect.

### `scythe scan` — discover projects and measure artifacts

Walks a directory tree, identifies project roots, and measures the
artifacts each one is sitting on. Read-only: nothing is ever deleted.

```bash
scythe scan .                                  # current directory
scythe scan ~/dev --depth 2                    # bound recursion depth
scythe scan ~/dev --only node,python           # filter by ecosystem
scythe scan ~/dev --older-than 30              # only artifacts older than 30 days
scythe scan ~/dev --min-size 500MB             # only artifacts at or above 500 MB
scythe scan ~/dev --format tree                # table | tree | compact | json
scythe scan ~/dev --format json -o report.json # also csv via .csv suffix
scythe scan /opt --follow-symlinks             # traverse symlinked dirs
scythe scan ~/dev --no-artifacts               # hide the artifact detail rows
```

| Flag                  | Type / default                  | Description                                                                                          |
|-----------------------|---------------------------------|------------------------------------------------------------------------------------------------------|
| `PATH` (positional)   | path, default `.`               | Directory to scan. Must exist.                                                                       |
| `--depth, -d`         | int, default `-1` (unbounded)   | Maximum recursion depth. `0` = scan only `PATH`, `1` = `PATH` and its immediate children, etc.       |
| `--follow-symlinks`   | flag, default off               | Follow symbolic links during traversal. Off by default to avoid loops on system trees.               |
| `--format`            | `table` \| `tree` \| `compact` \| `json` (default `table`) | How the result is rendered to stdout.                                       |
| `--output, -o`        | path                            | Also save the report to a file. `.json` → JSON; any other suffix → CSV.                              |
| `--no-artifacts`      | flag, default off               | Suppress the per-artifact detail rows in `table`/`tree` output (project totals only).                |
| `--only TYPES`        | comma-separated list            | Restrict to the named ecosystems. Canonical names (`node`, `python`, `rust`, `java_maven`, `java_gradle`, `go`, `ruby`, `dotnet`) and aliases (`py`, `js`, `rs`, `golang`, `.net`, `cs`) both accepted. |
| `--older-than DAYS`   | int, default `0` (off)          | Keep only artifacts whose `last_modified` is older than `DAYS` days.                                 |
| `--min-size SIZE`     | size string                     | Keep only artifacts at or above `SIZE`. Accepts raw bytes or human units: `512KB`, `100MB`, `1GB`.   |

### `scythe clean` — delete detected artifacts

Runs the same scan first, prints a summary, then either prompts
before deleting or executes immediately depending on flags. By default
deletion is permanent — files are unlinked, not moved to the OS bin.
Pass `--trash` to route them through scythe's recoverable trash
instead, then use `scythe restore` to bring them back.

```bash
scythe clean ~/dev --dry-run                   # simulate (always do this first)
scythe clean ~/dev --trash                     # recoverable cleanup (undo with `scythe restore`)
scythe clean ~/dev --interactive               # pick projects manually
scythe clean ~/dev --only rust                 # only Rust target/ directories
scythe clean ~/dev --older-than 30 --dry-run   # only target stale artifacts
scythe clean ~/dev --min-size 1GB --dry-run    # only large artifacts worth deleting
scythe clean ~/dev --force                     # skip the confirmation prompt
scythe clean ~/dev -o run-report.json          # export a JSON report
scythe clean ~/dev --depth 2 --follow-symlinks # bound the pre-clean scan
```

| Flag                  | Type / default                  | Description                                                                                                   |
|-----------------------|---------------------------------|---------------------------------------------------------------------------------------------------------------|
| `PATH` (positional)   | path, default `.`               | Directory to clean. Must exist.                                                                               |
| `--dry-run`           | flag, default off               | Simulate the deletion. The summary is rendered, sizes are reported, but nothing is touched. Recommended first.|
| `--interactive, -i`   | flag, default off               | After the scan, open a manual selector and let you pick which projects to clean.                              |
| `--force, -f`         | flag, default off               | Skip the "are you sure?" prompt. Useful for scripts and CI.                                                   |
| `--trash`             | flag, default off               | Move artifacts into scythe's recoverable trash instead of unlinking. Pair with `scythe restore` to undo.      |
| `--depth, -d`         | int, default `-1` (unbounded)   | Bound the preliminary scan's recursion depth.                                                                 |
| `--follow-symlinks`   | flag, default off               | Follow symlinks during the preliminary scan.                                                                  |
| `--only TYPES`        | comma-separated list            | Restrict to the named ecosystems. Same vocabulary as `scan`.                                                  |
| `--older-than DAYS`   | int, default `0` (off)          | Keep only artifacts older than `DAYS` days.                                                                   |
| `--min-size SIZE`     | size string                     | Keep only artifacts at or above `SIZE` (`100MB`, `1GB`, …).                                                   |
| `--output, -o`        | path                            | Save a JSON report of the clean run (artifacts deleted, size freed, errors, skipped).                         |

### `scythe restore` — undo a `clean --trash` run

```bash
scythe restore --list                  # show recoverable runs (id, date, items, size)
scythe restore                         # undo the most recent --trash run
scythe restore 20260502-153000-123456  # undo a specific run by id
```

| Flag / argument        | Description                                                                              |
|------------------------|------------------------------------------------------------------------------------------|
| `RUN_ID` (positional)  | Optional. Restore this specific run. Omit to target the most recent recoverable run.     |
| `--list`               | List recoverable runs (id, date, item count, total size, restored?) and exit.            |

Trashed runs live under the per-user data dir
(`%LOCALAPPDATA%\scythe` on Windows, `~/Library/Application Support/scythe`
on macOS, `$XDG_DATA_HOME/scythe` or `~/.local/share/scythe` on Linux).
A run that's already been restored, has a missing trash payload, or whose
destination has been re-created since the clean, is reported as *skipped*
rather than failing. OS-level failures during a restore are *errors* and
exit non-zero.

### `scythe ui` — interactive TUI

Full-screen alternative to `scan`/`clean` for exploration. Built on
[Textual](https://textual.textualize.io/), `scythe ui` shows two panes
side-by-side: a sortable, filterable list of cleanable projects on
the left, and the artifact list of the currently focused project on
the right. The status header surfaces the running totals
(`N projects · M/K artifacts · X.YZ GB to free`) so you always know
what a clean would reclaim.

```bash
scythe ui                                       # current directory
scythe ui ~/projects                            # specific path
scythe ui ~/projects --min-size 100MB           # focus on the heavy hitters
scythe ui . --only node,python --depth 3       # narrow the scan
scythe ui ~/dev --older-than 60                 # stale stuff only
scythe ui . --no-trash                          # delete directly instead of trashing
```

The scan runs **inside the TUI itself**. The Textual app opens
immediately with a `Scanning…` chip in the status bar and updates a
"N dirs · …/path/tail" progress line as directories are walked, on a
worker thread; the project list populates as soon as the scan
finishes. There's no Rich progress bar in front of the app anymore —
on big trees this removes the apparent startup latency.

The same scan filters as `scan`/`clean` are accepted and applied
before the project list is rendered.

| Flag                  | Type / default                  | Description                                                                                          |
|-----------------------|---------------------------------|------------------------------------------------------------------------------------------------------|
| `PATH` (positional)   | path, default `.`               | Directory to scan.                                                                                    |
| `--depth, -d`         | int, default `-1` (unbounded)   | Bound the recursion depth.                                                                            |
| `--follow-symlinks`   | flag, default off               | Follow symbolic links during the scan.                                                                |
| `--only TYPES`        | comma-separated list            | Restrict to the named ecosystems (same vocabulary as `scan`).                                         |
| `--older-than DAYS`   | int, default `0` (off)          | Keep only artifacts older than `DAYS` days.                                                           |
| `--min-size SIZE`     | size string                     | Keep only artifacts at or above `SIZE` (`100MB`, `1GB`, …).                                           |
| `--no-trash`          | flag, default off               | Delete directly when cleaning from the TUI. By default cleans go through the recoverable trash.       |

#### Keybindings

| Key       | Action                                                      |
|-----------|-------------------------------------------------------------|
| `space`   | Toggle the row under the cursor (project or single artifact)|
| `a`       | Toggle every artifact across every project                  |
| `Tab`     | Switch focus between the two panes                          |
| `s`       | Cycle sort: size · newest · type · path                     |
| `/`       | Filter the project list by path or type substring           |
| `Esc`     | Close/clear the filter                                      |
| `c`       | Clean the selected artifacts (asks for confirmation)        |
| `u`       | Undo the most recent clean run                              |
| `q`       | Quit                                                        |

#### Trash vs. direct delete

By default, cleans triggered from the TUI use **trash mode** —
artifacts are moved into scythe's recoverable trash dir rather than
permanently unlinked, and a per-run manifest is written. `u` (or
`scythe restore` from a regular shell) brings them back. Pass
`--no-trash` when launching the TUI to delete directly instead; the
confirmation dialog and the post-clean notification both reflect the
active mode so you can't mistake one for the other.

The CLI commands stay unchanged for scripts and CI; the TUI is for
interactive exploration.

### `scythe info`

Prints the installed version, a short feature summary, and the list of
supported ecosystems and artifact patterns. Takes no arguments.

```bash
scythe info
```

## Output

By default, `scythe` uses Rich ANSI-colored output for better readability.

Disable colored output using either the standard `NO_COLOR`
environment variable:

```bash
NO_COLOR=1 scythe scan ~/projects
```

or the top-level `--no-color` flag:

```bash
scythe --no-color scan ~/projects
```

This is useful for:
- screen readers
- CI logs
- terminals without ANSI support
- piping output to files or other tools

## Supported ecosystems

| Ecosystem      | Marker files                                                              | Artifact patterns                                                                                              |
|----------------|---------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| Node.js        | `package.json`, `yarn.lock`, `pnpm-lock.yaml`                             | `node_modules`, `dist`, `build`, `.next`, `.nuxt`, `out`, `.cache`, `.parcel-cache`, `.turbo`, `coverage`       |
| Python         | `requirements.txt`, `setup.py`, `pyproject.toml`, `Pipfile`, `poetry.lock`| `.venv`, `venv`, `env`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`, `*.egg-info`, `dist`, `build`, `.eggs`, `htmlcov` |
| Rust           | `Cargo.toml`, `Cargo.lock`                                                | `target`                                                                                                        |
| Java (Maven)   | `pom.xml`                                                                 | `target`, `.m2/repository`                                                                                      |
| Java (Gradle)  | `build.gradle`, `build.gradle.kts`, `settings.gradle`                     | `build`, `.gradle`, `out`                                                                                       |
| Go             | `go.mod`, `go.sum`                                                        | `bin`, `pkg`, `vendor`                                                                                          |
| Ruby           | `Gemfile`, `Gemfile.lock`, `.ruby-version`                                | `vendor/bundle`, `.bundle`, `tmp`                                                                               |
| .NET           | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln`                               | `bin`, `obj`, `packages`, `.vs`                                                                                 |

The `--only` flag accepts both canonical names (`node`, `python`,
`java_maven`, `java_gradle`, `dotnet`, ...) and short aliases (`py`,
`js`, `rs`, `golang`, `.net`, `cs`).

## Safety

- `clean` deletes via `shutil.rmtree` / `Path.unlink` — files are gone,
  not in the trash bin. Run `--dry-run` first when in doubt.
- Source-control dirs (`.git`, `.svn`, `.hg`, `.bzr`), editor metadata
  (`.idea`, `.vscode`), and OS metadata (`.DS_Store`, `Thumbs.db`) are
  skipped during traversal.
- Symlinks are not followed unless `--follow-symlinks` is passed.
- Use `--depth N` on very large filesystems to avoid runaway scans.

## Development

Python 3.10+ is required.

```bash
git clone https://github.com/elielMengue/scythe.git
cd scythe
pip install -e ".[dev]"

pytest -v                       # full test suite
pytest --cov=scythe             # with coverage
pytest tests/test_scanner.py    # a single file
```

CI runs the test suite on Linux, macOS, and Windows for Python 3.10,
3.11, and 3.12. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Contributing

Issues and pull requests are welcome.

To add support for a new ecosystem, extend two places:

- `PROJECT_MARKERS` in [`scythe/scanner/scanner.py`](scythe/scanner/scanner.py) — how to recognise the project.
- `ARTIFACT_PATTERNS` in [`scythe/detector/detector.py`](scythe/detector/detector.py) — what to clean.

Then add a fixture and an assertion in `tests/test_detector.py` that
exercises the new pattern. Keeping these two maps in sync is the core
invariant of the codebase.

## Roadmap

### Shipped
- [x] Configuration & foundations
- [x] Directory scanner
- [x] Artifact detection — 8 ecosystems
- [x] Rich-based output (table / tree / compact / JSON)
- [x] Cleaning engine (`--dry-run`, `--interactive`, `--force`, JSON report)
- [x] Filters: `--only`, `--older-than`, `--min-size`
- [x] **Recoverable trash + `scythe restore`** — `scythe clean --trash`
      moves artifacts under a per-user data dir and writes a per-run
      manifest; `scythe restore` undoes the most recent run (or a
      specific one by id). _(v0.6.0)_
- [x] **`scythe ui` — interactive TUI mode** (Textual) — full-screen
      browse-and-clean experience: project list with sort and filter,
      per-project artifact pane, item-level toggles, live total-size
      readout, and a trash-mode clean with in-app undo. _(v0.7.0)_
- [x] Distribution: PyPI (`pipx`), Docker (multi-arch GHCR)

### Safety & UX

### Filters & customization

- [ ] **`--ignore PATTERN`** — extra ignore patterns on top of the
      built-in defaults (e.g. `--ignore "*.archive,~/projects/keepme"`).
- [ ] **Config file** — `pyproject.toml [tool.scythe]` and/or
      `~/.scytherc` to persist `--only` / `--ignore` / depth defaults
      per machine.

### Distribution & polish

- [ ] **Standalone binaries** on GitHub Releases for users without Python:
  - macOS — Apple Silicon (`arm64`) and Intel (`x86_64`)
  - Linux — `x86_64` and `arm64` (glibc); musl/static build for Alpine
  - Windows — `x86_64` (`.exe`)
  - Optional: FreeBSD `x86_64`
- [ ] **Package-manager distribution** — Homebrew tap, Scoop bucket,
      winget manifest, and an AUR package.
- [ ] **Shell completions** — `scythe completion {bash,zsh,fish,powershell}`.

### Telemetry & quality

- [ ] **Lifetime stats** — track total space reclaimed across runs and
      surface it in `scythe info`.
- [ ] **Comprehensive integration tests** — broader scanner/cleaner
      coverage (large directory trees, permission edge cases,
      symlink loops).

See [CHANGELOG.md](CHANGELOG.md) for the release history.

## License

[MIT](LICENSE) © [Eliel MENGUE](https://github.com/elielMengue)
