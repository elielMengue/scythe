# Changelog

## [Unreleased]

## [0.7.1] - 2026-05-08

### Added
- **`scythe ui` accepts the same scan filters as `scan` and `clean`**:
  `--depth` / `-d`, `--follow-symlinks`, `--only`, `--older-than`,
  `--min-size`. Filters are applied to the in-memory `ScanResult`
  before the project list renders, so the TUI starts focused on
  exactly what you'd see from `scythe scan` with the same flags.
- **`scythe ui --no-trash`** — opt out of trash mode for cleans
  triggered from the TUI. With this flag, `c` deletes artifacts
  directly via `ArtifactCleaner` instead of routing through
  `TrashMover`. The confirmation dialog and the post-clean notification
  both reflect the active mode so the two paths are unambiguous.

### Changed
- **TUI launches immediately**: `scythe ui` no longer runs the Rich
  progress bar before opening the Textual app. The scan is now driven
  by a Textual `@work` thread; the header shows a `Scanning…` chip and
  a per-directory progress line via `call_from_thread`, and the
  project list populates when the worker finishes. On large trees this
  removes the apparent startup latency. The CLI signature for `ui` is
  unchanged.

### Documentation
- README: new **Global options** subsection (`--verbose`, `--no-log-file`,
  `--version`, `--help`) and per-command **Flags** tables for `scan`,
  `clean`, `restore`, and `ui`. Every flag is now documented with its
  type, default, and behavior; previously undocumented options
  (`--follow-symlinks` on `scan`/`clean`/`ui`, `--no-artifacts` on
  `scan`, `--depth` on `clean`) are now listed. The `scythe ui` section
  was rewritten to cover the new flags, the in-app worker-driven scan,
  and a dedicated "Trash vs. direct delete" paragraph.

### Technical
- Release v0.7.1.

## [0.7.0] - 2026-05-04

### Added
- **`scythe ui` — interactive TUI mode** (Textual). Full-screen
  alternative to `scan`/`clean` for exploration. Two side-by-side
  panes: a project list on the left (sortable by size · newest · type
  · path, filterable by substring) and the artifact list of the
  focused project on the right. The header surfaces running totals
  (`N projects · M/K artifacts · X.YZ GB to free`).
  - `space` toggles the row under the cursor (a project, full or
    partial; or a single artifact); `a` toggles every artifact.
  - `Tab` switches focus between panes.
  - `s` cycles sort modes; `/` opens a filter input (Esc to close).
  - `c` runs the selected artifacts through `ArtifactCleaner` in
    **trash mode** (recoverable) after a confirmation modal; `u`
    restores the most recent run.
  - The CLI gains a `scythe ui [PATH]` subcommand. Textual is loaded
    lazily so non-TUI commands keep their cold-start time.
- New `scythe.tui` package (`ScytheApp`, `run_tui`,
  `ConfirmCleanScreen`). Twelve Pilot-driven smoke and interaction
  tests cover boot, the empty case, default selection, project- and
  artifact-level toggles (with partial-state assertion), toggle-all,
  sort cycling and ordering, filter narrowing, confirm-and-trash on a
  real on-disk artifact, cancel, and undo with no runs.

### Changed
- `.gitignore` broadened to exclude `__pycache__/`, `*.pyc`, `*.pyo`,
  `.pytest_cache/`, and `.pytest_tmp/`.

## [0.6.1] - 2026-05-03

### Changed
- **Console rendering for `scan` and `clean` rebuilt around a shared
  template**: a context header (command + path + active filter chips),
  a one-line headline (`Found N project(s) · X.YZ GB reclaimable`),
  the projects body (lighter table with header rule only, no
  surrounding box), and a one-line dim footer with stats. The
  standalone "Statistics" and "Cleaning results" tables are gone —
  their content collapses into the new footers. Filter feedback
  (`--only`, `--older-than`, `--min-size`) is no longer printed
  between the progress bar and the headline; it's logged at INFO.

### Added
- **Live counters in the scan/clean progress bar**:
  - Scan: `Scanning N dirs · <truncated current path>` updates per
    directory walked, on a transient indeterminate spinner.
  - Clean: determinate progress with `M/N` projects, bar, and
    elapsed time, also transient.
  Both bars erase themselves on completion so the final headline is
  the focal point.

### Fixed
- Residual French strings purged from console output (banner
  docstring, formatter error message, interactive-selection table
  columns, several test docstrings) and a handful of typos
  (`Scand ends in` → `Scan completed in`, `Cleaning end in` →
  `Cleaning completed in`, `Errors that occurs` → `Errors`).
- French-style spacing before `:` and `?` removed throughout user-
  facing strings.

### Planned — Safety & UX
- **`scythe ui` — interactive TUI mode** (Textual): full-screen
  browse-and-clean experience with a filterable project list, expandable
  artifact tree, live total-size readout, item-level toggles, and an
  undo stack that pairs with trash-mode. The CLI stays for scripts/CI;
  the TUI is for exploration.

### Planned — Filters & customization
- **`--ignore PATTERN`**: extra ignore patterns on top of the built-in
  defaults.
- **Config file**: `pyproject.toml [tool.scythe]` and/or `~/.scytherc`
  for persistent defaults.

### Planned — Distribution & polish
- **Standalone binaries** on GitHub Releases for users without Python:
  - macOS (`arm64` + `x86_64`)
  - Linux (`x86_64` glibc, `x86_64` musl static, `arm64`)
  - Windows (`x86_64` `.exe`)
- **Package-manager distribution**: Homebrew tap, Scoop bucket, winget
  manifest, AUR.
- **Shell completions**: `scythe completion {bash,zsh,fish,powershell}`.

### Planned — Telemetry & quality
- **Lifetime stats** surfaced in `scythe info`.
- **Comprehensive integration tests** for scanner/cleaner edge cases.

## [0.6.0] - 2026-05-02

### Added
- **`scythe clean --trash`** — recoverable cleanup. Instead of
  unlinking, artifacts are moved to a per-run directory under the
  per-user data dir (`%LOCALAPPDATA%\scythe` on Windows,
  `~/Library/Application Support/scythe` on macOS,
  `$XDG_DATA_HOME/scythe` or `~/.local/share/scythe` on Linux), and
  a JSON manifest records every move. The CLI prints the run id and
  manifest path, and the existing "deletion is PERMANENT" warning is
  now scoped to runs WITHOUT `--trash`.
- **`scythe restore`** — undo a `clean --trash` run.
  - `scythe restore --list` shows recoverable runs (id, date,
    item count, total size, whether already restored).
  - `scythe restore` (no args) restores the most recent run.
  - `scythe restore <RUN_ID>` targets a specific run.
  - Skip vs error are surfaced separately: a destination that
    already exists or a missing trash payload is a skip; OS-level
    failures are errors (non-zero exit).
- **`scythe.trash` module** — new internal API: `TrashMover`,
  `RunManifest`, `TrashedItem`, `get_trash_root`, `new_run_id`,
  `list_runs`, `load_manifest`, `restore_run`. Reusable by the
  upcoming TUI mode.
- 19 new tests covering platform-specific data-dir resolution, name
  collisions, manifest shape, skip vs error paths, end-to-end
  `--trash` wiring, and `restore` round-trip.

### Changed
- `ArtifactCleaner` and `clean_artifacts` accept an optional
  `trash_mover`; the cleaner threads `project_type` through
  `clean_project` so the manifest can record it.
- `clean` docstring: `--trash` now listed under Operating Modes.

### Technical
- Release v0.6.0.

## [0.5.3] - 2026-05-02

### Added
- **`--min-size SIZE` filter** on both `scan` and `clean` commands.
  Keeps only artifacts at or above the given size threshold, with support
  for raw bytes as well as human-readable units such as `512KB`, `100MB`,
  and `1GB`.
  - Examples:
    - `scythe scan ~/projects --min-size 500MB`
    - `scythe clean ~/projects --min-size 1GB --dry-run`
- `parse_size_threshold` and `filter_projects_by_artifact_size` helpers in
  `scythe/utils/utils.py`, designed to narrow artifact lists without
  mutating the original project objects.
- Targeted tests for size parsing, artifact-size filtering, and CLI
  behavior on both `scan` and `clean`.

### Changed
- README usage examples and roadmap notes now document `--min-size` as a
  shipped advanced filter.

### Technical
- Release v0.5.3

## [0.5.2] - 2026-05-02

### Added
- **`--older-than DAYS` filter** on both `scan` and `clean` commands.
  Drops projects whose artifacts are all more recent than the cutoff, and
  within kept projects narrows the artifact list to the ones older than
  the cutoff. Backed by `filter_projects_by_artifact_age` in
  `scythe/utils/utils.py` (with an injectable `now` for deterministic
  tests).
  - Example: `scythe clean ~/projects --older-than 30 --dry-run`
- `--follow-symlinks` flag on `clean` (was missing — `scan` already had it,
  so the two commands disagreed on symlinked trees).
- `tests/test_utils.py`: covers the new age filter (boundary, mutation
  safety, recent-only drop, mixed-age narrowing) plus regression tests for
  `format_size` and `is_ignored_path`.
- Contributor onboarding: `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
  and `.github/ISSUE_TEMPLATE/` (bug report, feature request, config).

### Fixed
- `clean` command had three bugs that any real interactive run would have
  hit:
  - `selected_projects = interactive_select_project` followed by a bare
    `(project_with_artifacts, scan_path)` tuple on the next line — the
    function was never called and `selected_projects` was bound to the
    function object. `--interactive` is now functional.
  - Stray `global output_path` at the top of `clean` leaked module-level
    state across invocations.
  - The post-clean "Errors:" header and its loop were outside the
    `if clean_result.errors:` guard, so an empty Errors section was
    printed on every successful run.
- `display_tree_view` (Rich tree output): the `defaultdict` grouping
  reset the per-type list on every duplicate key, so only the *last*
  project per ecosystem rendered. Now correctly groups all projects.
  Tree nodes also format sizes (`1.00 MB`) instead of raw byte ints.

### Technical
- Test suite: 33 → 42 passing.
- Release v0.5.2

## [0.1.0] - 2025-01-29

### Added
- Initial CLI structure with Click
- Rich logging system (console + file)
- Basic commands: scan, clean, info
- Unit tests for CLI 
- Project documentation

##  [0.1.0] - 2025-01-30

### Changed 

-   setup.py -> pyproject.toml

### Added 

-   Scan Feature
  - Test for scan and models


## [0.2.0] - 2025-01-31

### Added
-  **Directory Scanner** - Scan récursif de répertoires
-  **Project Detection** - Détection automatique de 8 types de projets :
  - Node.js (package.json, yarn.lock, pnpm-lock.yaml)
  - Python (requirements.txt, setup.py, pyproject.toml, Pipfile)
  - Rust (Cargo.toml)
  - Java Maven (pom.xml)
  - Java Gradle (build.gradle)
  - Go (go.mod)
  - Ruby (Gemfile)
  - .NET (*.csproj, *.sln)


### Fixed
- Logger initialization avec arguments corrects
- RichHandler typo (`tracebacks_show_locals`)
- Project dataclass avec `project_type` (singulier)
- DateTime default factory pour éviter les erreurs de mutation

### Technical
- Scan with configurable depth (`--depth`)
- Erros handling (permissions, chemins invalides)
- Patterns ignored (.git, .svn, .idea, etc.)

### Coming Next
- [x] Detection and calculation of artefacts (node_modules, .venv, target/, etc.) **Done**

## [0.2.0] - 2025-02-02

### Added 
- Artifact detector and size calculation

## [0.2.0] - 2025-05-02

### Added

- Scan format (tree, table, json)
- Report generation in two formats (csv & json) 
- Add new option to the cli : command example `scythe scan /project_path --format [tree, table, json]` this helps format the scan result in a better way we want it to.
`scythe scan /project_path --output report_file` this command will generate a report after the scan complete. Notice that the report file support only two types : **csv** and **json**
- Release v0.3.0

## [0.5.1] - 2026-05-01

### Changed
- **PyPI distribution renamed** to `artifact-scythe` (the name `scythe` is taken
  on PyPI). The Python module and the installed command remain `scythe`,
  so user-facing usage is unchanged. Install becomes `pip install artifact-scythe`.
- README badges and install snippet updated accordingly. Release workflow
  environment URL points at https://pypi.org/p/artifact-scythe.

### Fixed
- **Windows CI smoke test** crashed with `UnicodeEncodeError` on cp1252
  when Rich rendered the braille spinner (`U+2838`) and box-drawing
  characters. Setting `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` at the
  workflow level forces UTF-8 stdio across all jobs. Reproduced and
  validated locally on Windows 11.
- `banner.VERSION` was hardcoded to `0.3.0`; now mirrors
  `scythe.__version__` so `scythe info` reports the real version.
- Banner ASCII art switched to a raw string to silence the
  invalid-escape `SyntaxWarning` raised on Python 3.12+.

### Technical
- First release pipeline run end-to-end (CI matrix → PyPI publish via
  Trusted Publishing → GitHub Release with auto-generated notes).
- Release v0.5.1

## [0.5.0] - 2026-05-01

### Added
- **`--only TYPES` filter** on both `scan` and `clean` commands. Accepts a
  comma-separated list of project types (canonical values like `node`,
  `python`, `rust`, `java_maven`, `java_gradle`, `go`, `ruby`, `dotnet`, or
  short aliases like `py`, `js`, `rs`, `golang`, `.net`, `cs`).
  - Example: `scythe clean ~/projects --only node,python --dry-run`
- `ProjectType.from_alias` classmethod that resolves a user-supplied string
  to a `ProjectType`, raising a clear error listing valid types on a typo.
- Unit tests covering canonical names, short aliases, case/whitespace
  insensitivity, and the unknown-alias error path.

### Fixed
- **Critical scanner bug**: `_scan_recursive` used `global project, artifacts`
  and unconditionally appended `project` even when the current directory had
  no marker file. This raised `NameError` on the first call for any non-project
  root, which was silently swallowed by the outer try/except so users saw 0
  projects with no surface error. Rewritten to use local variables and only
  append when a project is actually detected.
- Renamed test fixture `node_project_with_artifact` → `node_project_with_artifacts`
  so that `test_detect_artifacts_node` resolves correctly.

### Technical
- Test suite: 29 → 33 passing.
- Release v0.5.0

## [0.4.0] - 2026-02-06

### Added
- **Cleaning Engine** - Real artifact deletion built on top of the scanner/detector pipeline
  - `ArtifactCleaner` class handles per-project and per-artifact removal with full error/skip tracking
  - `CleanResult` dataclass aggregates deletion stats (artifacts deleted, space freed, success rate, duration)
  - `safe_delete` helper for one-off path removal
- **`scythe clean` CLI command** with the following modes:
  - `--dry-run` : simulation, reports what would be freed without touching the disk
  - `--interactive` / `-i` : manual selection of projects to clean
  - `--force` / `-f` : skip confirmation prompt (for scripts/automation)
  - `--depth` / `-d` : bound the preliminary scan
  - `--output` / `-o` : export a JSON report of the clean run
- Two-step UX: scan first, then confirm before deletion. Summary table rendered with Rich (cleaned projects, artifacts deleted, freed memory, success rate, errors, skipped).
- Unit tests for the cleaner (`tests/test_cleaner.py`)

### Technical
- Permission/OSError/unknown-error paths are captured in `CleanResult.errors` instead of raising
- Missing artifacts at deletion time are recorded in `CleanResult.skipped` rather than failing
- Release v0.4.0
