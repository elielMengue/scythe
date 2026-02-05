"""
    Artifact Detector
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime

from scythe.models.models import ProjectType, ArtifactInfo
from scythe.utils.utils import calculate_directory_size
from scythe.logger.logger import get_logger

# Artifacts matches project type

ARTIFACT_PATTERNS: Dict[ProjectType, List[str]] = {
    ProjectType.NODE: [
        'node_modules',
        'dist',
        'build',
        '.next',
        '.nuxt',
        'out',
        '.cache',
        '.parcel-cache',
        '.turbo',
        'coverage'
    ],

    ProjectType.PYTHON: [
        '.venv',
        'venv',
        'env',
        '__pycache__',
        '.pytest_cache',
        '.mypy_cache',
        '.ruff_cache',
        '.tox',
        '*.egg-info',
        'dist',
        'build',
        '.eggs',
        'htmlcov',
        '.coverage'
    ],

    ProjectType.RUST: [
        'target'
    ],

    ProjectType.JAVA_MAVEN: [
        'target',
        '.m2/repository'
    ],

    ProjectType.JAVA_GRADLE: [
        'build',
        '.gradle',
        'out'
    ],

    ProjectType.GO: [
        'bin',
        'pkg',
        'vendor'
    ],

    ProjectType.RUBY: [
        'vendor/bundle',
        '.bundle',
        'tmp'
    ],

    ProjectType.DOTNET: [
        'bin',
        'obj',
        'packages',
        '.vs'
    ]
}

class ArtifactDetector :
    """
        Detect artifact

        Attributes :
        project_path, project_type, follow_symlinks
    """


    def __init__(
            self,
            project_path: Path,
            project_type: ProjectType,
            follow_symlinks: bool = False
    ) :
        self.project_path = project_path
        self.project_type = project_type
        self.follow_symlinks = follow_symlinks
        self.logger = get_logger()

    def get_artifact_pattern(self) -> List[str]:

        return ARTIFACT_PATTERNS.get(self.project_type, [])

    def is_artifact(self, path: Path) -> bool:
        patterns = self.get_artifact_pattern()

        for pattern in patterns :
            if '*' in pattern :
                extension = pattern.replace('*', '')
                if path.name.endswith(extension) :
                    return True
            elif path.name == pattern :
                return True

        return False


    def detect_artifacts(self) -> List[ArtifactInfo]:
        artifacts = []

        if not self.project_path.exists() or not self.project_path.is_dir() :
            self.logger.warning(f"Invalid Project: {self.project_path}")
            return artifacts

        try:
            for item in self.project_path.iterdir() :
                if item.is_symlink()  and not self.follow_symlinks :
                    continue


                if item.is_dir() and self.is_artifact(item) :
                    artifact_info = self._create_artifact_info(item)
                    if artifact_info :
                        artifacts.append(artifact_info)
                        self.logger.debug(
                            f"Detected Artifact : {item.name}"
                            f"({artifact_info.size_formatted})"
                        )

                elif item.is_file() and self.is_artifact(item) :
                    artifact_info = self._create_artifact_info(item)
                    if artifact_info :
                        artifacts.append(artifact_info)

        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot access the dir : {self.project_path}")

        return artifacts


    def _create_artifact_info(self, path: Path) -> ArtifactInfo | None:

        try:
            if path.is_dir() :
                size = calculate_directory_size(path, self.follow_symlinks)
            else :
                size = path.stat().st_size

            last_modified = datetime.fromtimestamp(path.stat().st_mtime)

            return ArtifactInfo(
                path = path,
                size_bytes=size,
                last_modified=last_modified,
                artifact_type=path.name

            )

        except (OSError, PermissionError) as e:
            self.logger.debug(f"Impossible to calculate the size of {path}: {e}")
            return None



def detect_artifacts(
        project_path: Path,
        project_type: ProjectType,
        follow_symlinks: bool = False
) -> List[ArtifactInfo] :

    detector = ArtifactDetector(project_path, project_type, follow_symlinks)
    return detector.detect_artifacts()
