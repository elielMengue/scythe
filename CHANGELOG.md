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
- Scan avec profondeur configurable (`--depth`)
- Support des liens symboliques (`--follow-symlinks`)
- Gestion robuste des erreurs (permissions, chemins invalides)
- Patterns ignorés (.git, .svn, .idea, etc.)

### Coming Next
- Détection et calcul des artefacts (node_modules, .venv, target/, etc.) 

