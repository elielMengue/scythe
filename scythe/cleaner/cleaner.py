"""
Cleaner of Artifacts
"""

import shutil
import time
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

from scythe.models.models import Project, ArtifactInfo, CleanResult
from scythe.logger.logger import get_logger

class ArtifactCleaner:

    """
    Clean Artifacts

    Attributes
    dry_run
    verbose
    progress_callback
    """

    def __init__(
            self,
            dry_run: bool = False,
            verbose: bool = False,
            progress_callback: Optional[Callable[[str], None]] = None,
    ):

        self.dry_run = dry_run
        self.verbose = verbose
        self.progress_callback = progress_callback
        self.logger = get_logger()

        self.artifacts_deleted = 0
        self.space_freed = 0
        self.errors: List[str] = []
        self.skipped: List[str] = []

    def clean_projects(self, projects: List[Project]) -> CleanResult:
        start_time = time.time()

        if self.dry_run :
            self.logger.info(f"Dry-run enabled - simulation mode")
        self.logger.info(f"Cleaning {len(projects)} projects")

        self.artifacts_deleted = 0
        self.space_freed = 0
        self.errors = []
        self.skipped = []

        projects_cleaned = []

        for project in projects:
            if self.progress_callback :
                self.progress_callback(f"Cleaning {project.path.name}")

            if self.clean_project(project):
                projects_cleaned.append(project)

        clean_duration = time.time() - start_time

        result = CleanResult(
            projects_cleaned=projects_cleaned,
            artifacts_deleted=self.artifacts_deleted,
            space_freed=self.space_freed,
            errors=self.errors,
            skipped=self.skipped,
            clean_duration=clean_duration,
            dry_run=self.dry_run
        )

        self.logger.info(
            f"Clean ends in {clean_duration:.2f}s - "
            f"{self.artifacts_deleted} artifacts deleted"
        )

        return result

    def clean_project(self, project: Project)-> bool:
        if not project.artifacts:
            self.logger.debug(f"Noting to clean in {project.path}")
            return False

        cleaned = False

        for artifact in project.artifacts :
            if self.clean_artifact(artifact) :
                cleaned = True

        return cleaned


    def clean_artifact(self, artifact: ArtifactInfo)-> bool:
        artifact_path = artifact.path

        try:
            if not artifact_path.exists() : #Check a valid path
                self.logger.debug(f"Artifact removed: {artifact_path}")
                self.skipped.append(str(artifact_path))
                return False

            #Simulation
            if self.dry_run :
                self.logger.info(f"[DRY-RUN] Removing {artifact_path}")
                self.artifacts_deleted +=1
                self.space_freed += artifact.size_bytes
                return True

            #Real world removing :)
            if artifact_path.is_dir():
                self._delete_directory(artifact_path)
            else:
                self._delete_file(artifact_path)

            self.artifacts_deleted +=1
            self.space_freed += artifact.size_bytes

            self.logger.info(f"✓ Deleted : {artifact_path}")

            return True

        except PermissionError as e :
            error_msg = f"Permission Denied: {artifact_path}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False

        except OSError as e :
            error_msg = f"Can\'t remove {artifact_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False

        except Exception as e:
            error_msg = f"Unknown error {artifact_path}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    @staticmethod
    def _delete_directory(path: Path)-> None:

        if not path.is_dir() :
            raise ValueError(f"Not a directory: {path}")

        shutil.rmtree(path, ignore_errors=False)

    def _delete_file(self, path: Path)-> None:

        if not path.is_file() :
            raise ValueError(f"Not a file: {path}")

        path.unlink()


def clean_artifacts(
        projects: List[Project],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> CleanResult:

        cleaner = ArtifactCleaner(
            dry_run=dry_run,
            progress_callback=progress_callback
        )
        return cleaner.clean_projects(projects)


def safe_delete(path: Path, dry_run: bool = False) -> bool:

        if dry_run:
            return path.exists()

        try:
            if path.is_dir() :
                shutil.rmtree(path)
            elif path.is_file() :
                path.unlink()
            else:
                return False

            return True

        except (OSError, PermissionError) as e:
            return False



