
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
        except (OSError, PermissionError):
            pass

        return found_markers

    def should_skip_directory(self, directory: Path, current_depth: int) -> bool:

        if self.max_depth >= 0 and current_depth > self.max_depth :
            return True

        if is_ignored_path(directory, self.custom_ignores):
            return True

        if directory.is_symlink() and not self.follow_symlinks:
            return True

        return False

    def scan(self) -> ScanResult:

        self.logger.info(f"Scanning directory {self.root_path}")
        start_time = time.time()

        #Stats
        self.directories_scanned = 0
        self.files_scanned = 0
        self.errors = []

        projects = []

        #recursive scan
        try:
            projects = self._scan_recursive(self.root_path, depth=0)
        except Exception as e:
            self.logger.error(f"Fatal Error while Scanning : {e}")
            self.errors.append(f"Fatal Error: {str(e)}")

        scan_duration = time.time() - start_time
        result = ScanResult(
            root_path=self.root_path,
            projects=projects,
            scan_duration=scan_duration,
            directories_scanned=self.directories_scanned,
            files_scanned=self.files_scanned,
            errors=self.errors,
        )

        self.logger.info(
            f"Scan Ends in {scan_duration:.2f}s-"
            f"{result.total_projects} projects founds"
        )

        return result

    def _scan_recursive(
            self,
            directory: Path,
            depth: int,
            parent_has_artifacts: bool = False,) -> List[Project]:

        projects = []

        if self.should_skip_directory(directory, depth):
            return projects

        self.directories_scanned += 1

        if self.progress_calback:
            self.progress_calback(f"Scanning {directory}")

        project_type = self.detect_project_type(directory)

        if project_type :
            self.logger.debug(f"Found project type {project_type} detected in : {directory}")

            markers_files = self.get_marker_files(directory, project_type)
            project = Project(
                path=directory,
                project_type=project_type,
                markers_files=markers_files,
                artifacts=[] #Coming Soon TODO
            )

        projects.append(project)

        try:
            for item in directory.iterdir():
                if item.is_dir():
                    if not is_ignored_path(item, self.custom_ignores):
                        sub_projects = self._scan_recursive(item, depth+1, parent_has_artifacts=parent_has_artifacts)
                        projects.extend(sub_projects)
                elif item.is_file():
                    self.files_scanned += 1
        except (OSError, PermissionError) as e:
            error_msg = f"Error accessing directory {directory}: {e}"
            self.logger.warning(error_msg)
            self.errors.append(error_msg)

        return projects

def scan_directory(
        path: Path,
        max_depth: int = -1,
        follow_symlinks: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None) -> ScanResult:
    scanner = DirectoryScanner(
        root_path=path,
        max_depth=max_depth,
        follow_symlinks=follow_symlinks,
        progress_calback=progress_callback
    )

    return scanner.scan()

