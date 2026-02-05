"""
Testing Models
"""

from pathlib import Path
from datetime import datetime

from scythe.models.models import ProjectType, ArtifactInfo, Project, ScanResult


def test_project_type_enum():
    assert ProjectType.NODE.value == "node"
    assert ProjectType.PYTHON.value == "python"
    assert ProjectType.NODE.display_name == "Node.js"


def test_artifact_info_creation():
    artifact = ArtifactInfo(
        path=Path("/test/node_modules"),
        size_bytes=1024 * 1024,  # 1 MB
        last_modified=datetime.now(),
        artifact_type="node_modules"
    )

    assert artifact.path == Path("/test/node_modules")
    assert artifact.size_bytes == 1024 * 1024
    assert "MB" in artifact.size_formatted


def test_project_creation():
    project = Project(
        path=Path("/test/my-app"),
        project_type=ProjectType.NODE,
        marker_files=["package.json"],
        artifacts=[]
    )

    assert project.path == Path("/test/my-app")
    assert project.project_type == ProjectType.NODE
    assert project.artifact_count == 0
    assert project.total_artifact_size == 0


def test_project_with_artifacts():
    artifact1 = ArtifactInfo(
        path=Path("/test/node_modules"),
        size_bytes=1024 * 1024,
        last_modified=datetime.now(),
        artifact_type="node_modules"
    )

    artifact2 = ArtifactInfo(
        path=Path("/test/dist"),
        size_bytes=512 * 1024,
        last_modified=datetime.now(),
        artifact_type="dist"
    )

    project = Project(
        path=Path("/test/my-app"),
        project_type=ProjectType.NODE,
        marker_files=["package.json"],
        artifacts=[artifact1, artifact2]
    )

    assert project.artifact_count == 2
    assert project.total_artifact_size == (1024 * 1024) + (512 * 1024)


def test_scan_result_creation():
    result = ScanResult(
        root_path=Path("/test"),
        projects=[],
        scan_duration=1.5,
        directories_scanned=100,
        files_scanned=500
    )

    assert result.total_projects == 0
    assert result.scan_duration == 1.5


def test_scan_result_summary():
    project = Project(
        path=Path("/test/app"),
        project_type=ProjectType.PYTHON,
        marker_files=["requirements.txt"]
    )

    result = ScanResult(
        root_path=Path("/test"),
        projects=[project],
        directories_scanned=50,
        files_scanned=200
    )

    summary = result.get_summary()
    assert summary['total_projects'] == 1
    assert summary['directories_scanned'] == 50
    assert summary['python_projects'] == 1