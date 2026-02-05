# Changelog

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
- [x] Detection and calculation of artefacts (node_modules, .venv, target/, etc.)

## [0.2.0] - 2025-02-02

### Added 
- Artifact detector and size calculation

## [0.2.0] - 2025-05-02

### Added

- Scan format (tree, table, json)
- Report generation in two formats (csv & json) 
- Add new option to the cli : command example `scythe scan /project_path --format [tree, table, json]` this helps format the scan result in a better way we want it to.
`scythe scan /project_path --output report_file` this command will generate a report after the scan complete. Notice that the report file support only two types : **csv** and **json**
