"""
Test for cleaner
"""

import pytest
from pathlib import Path
from datetime import datetime
from scythe.models.models import ArtifactInfo, Project, ProjectType
from scythe.cleaner.cleaner import ArtifactCleaner, clean_artifacts, safe_delete

@pytest.fixture
def temp_artifact(tmp_path):
    """Temporary artifact for testing"""
    artifact_dir = tmp_path / "node_modules"
    artifact_dir.mkdir()

    (artifact_dir / "package1").mkdir()
    (artifact_dir / "package1" / "index.js").write_text("module.exports = {}")
    (artifact_dir / "package2").mkdir()
    (artifact_dir / "package2" / "lib.js").write_text("exports.lib = {}")

    return artifact_dir
@pytest.fixture
def project_with_artifact(temp_artifact) :
    """Create temporary project for testing"""
    project_path = temp_artifact.parent

    artifact = ArtifactInfo(
        path=temp_artifact,
        size_bytes=1024 * 100,  # 100 KB
        last_modified=datetime.now(),
        artifact_type="node_modules"
    )

    project = Project(
        path=project_path,
        project_type=ProjectType.NODE,
        marker_files=["package.json"],
        artifacts=[artifact]
    )

    return project


def test_clean_artifact_dry_run(project_with_artifact):
    """Test in dry-run mode"""
    cleaner = ArtifactCleaner(dry_run=True)
    artifact = project_with_artifact.artifacts[0]

    assert artifact.path.exists()
    result = cleaner.clean_artifact(artifact)

    assert result == True
    assert cleaner.artifacts_deleted == 1
    assert cleaner.space_freed == artifact.size_bytes

    assert artifact.path.exists()


def test_clean_artifact_real(project_with_artifact):
    """Test with real mode"""
    cleaner = ArtifactCleaner(dry_run=False)
    artifact = project_with_artifact.artifacts[0]

    assert artifact.path.exists()

    result = cleaner.clean_artifact(artifact)

    assert result == True
    assert cleaner.artifacts_deleted == 1

    assert not artifact.path.exists()


def test_clean_project(project_with_artifact):
    """cleaning project"""
    cleaner = ArtifactCleaner(dry_run=False)

    result = cleaner.clean_project(project_with_artifact)

    assert result == True
    assert cleaner.artifacts_deleted == 1


def test_clean_projects_multiple(tmp_path):
    """Cleaning multiple projects"""
    projects = []

    for i in range(2):
        project_dir = tmp_path / f"project-{i}"
        project_dir.mkdir()

        artifact_dir = project_dir / "node_modules"
        artifact_dir.mkdir()
        (artifact_dir / "lib.js").write_text("code")

        artifact = ArtifactInfo(
            path=artifact_dir,
            size_bytes=1000,
            last_modified=datetime.now(),
            artifact_type="node_modules"
        )

        project = Project(
            path=project_dir,
            project_type=ProjectType.NODE,
            artifacts=[artifact]
        )

        projects.append(project)

    cleaner = ArtifactCleaner(dry_run=False)
    clean_result = cleaner.clean_projects(projects)

    assert clean_result.artifacts_deleted == 2
    assert len(clean_result.projects_cleaned) == 2


def test_clean_artifact_already_deleted(project_with_artifact):
    """Test with artifacts already deleted"""
    cleaner = ArtifactCleaner()
    artifact = project_with_artifact.artifacts[0]
    import shutil
    shutil.rmtree(artifact.path)

    result = cleaner.clean_artifact(artifact)

    assert result == False
    assert len(cleaner.skipped) == 1


def test_safe_delete_directory(tmp_path):
    """Test safe_delete"""
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")

    assert test_dir.exists()

    result = safe_delete(test_dir, dry_run=False)

    assert result == True
    assert not test_dir.exists()


def test_safe_delete_file(tmp_path):
    """Test safe_delete with files"""
    test_file = tmp_path / "file.txt"
    test_file.write_text("content")

    assert test_file.exists()

    result = safe_delete(test_file, dry_run=False)

    assert result == True
    assert not test_file.exists()