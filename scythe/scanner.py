
import os
from pathlib import Path
from typing import List, Optional, Callable, Set
import time

from scythe.models import Project, ProjectType, ScanResult, ArtifactInfo
from scythe.utils import (
is_ignored_path,
calculate_directory_size,
IGNORED_PATTERNS
)

from scythe.logger import get_logger

PROJECT_MARKERS = {
    ProjectType.NODE: ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
    ProjectType.PYTHON: ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock'],
    ProjectType.RUST: ['Cargo.toml', 'Cargo.lock'],
    ProjectType.JAVA_MAVEN: ['pom.xml'],
    ProjectType.JAVA_GRADLE: ['build.gradle', 'build.gradle.kts', 'settings.gradle'],
    ProjectType.GO: ['go.mod', 'go.sum'],
    ProjectType.RUBY: ['Gemfile', 'Gemfile.lock', '.ruby-version'],
    ProjectType.DOTNET: ['*.csproj', '*.fsproj', '*.vbproj', '*.sln']
}

class DirectoryScanner :
    def __init__(self,
                 root_path: Path,
                 max_depth: -1,
                 follow_symlinks: bool = False,
                 custom_ignores: Optional[Set[str]] = None,
                 progress_calback: Optional[Callable[[str], None]] = None):
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.follow_symlinks = follow_symlinks
        self.custom_ignores = custom_ignores or Set()
        self.progress_calback = progress_calback
        self.logger = get_logger()

        #Stats

        self.directories_scanned = 0
        self.files_scanned = 0
        self.errors: List[str] = []


    def detect_project_type(self, directory: Path) -> Optional[ProjectType]:
        if not directory.is_dir():
            return None

        try:
            files_in_dir = {f.name for f in directory.iterdir() if f.is_file() }
        except (OSError, PermissionError) as e:
            self.logger.debug(f"Impossible to read directory {directory}: {e}")
            return None

        for project_type, markers in PROJECT_MARKERS.items():
            for marker in markers:
                if '*' in marker:
                    extension = marker.replace('*', '')
                    if any(f.endswith(extension) for f in files_in_dir):
                        return project_type
                elif marker in files_in_dir:
                    return project_type
        return None

    def get_marker_files(self, directory: Path, project_type: ProjectType) -> List[str]:
        found_markers = []
        markers = PROJECT_MARKERS.get(project_type, [])

        try:
            files_in_dir = {f.name for f in directory.iterdir() if f.is_file()}
            for marker in markers :
                if '*' in marker:
                    extension = marker.replace('*', '')
                    found_markers.extend([f for f in files_in_dir if f.endswith(extension)])
                elif marker in files_in_dir:
                    found_markers.append(marker)
        except (OSError, PermissionError)
            pass

        return found_markers