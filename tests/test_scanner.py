"""
Unit tests for scanner command
"""

import pytest
from pathlib import Path

from scythe.scanner.scanner import DirectoryScanner, scan_directory
from scythe.models.models import ProjectType

@pytest.fixture
def test_project_structure(tmp_path):
    node_project = tmp_path / "node-app"
    node_project.mkdir()
    (node_project / "package.json").write_text('{"name": "test"}')
    (node_project / "node_modules").mkdir()

    python_project = tmp_path / "python-app"
    python_project.mkdir()
    (python_project / "requirements.txt").write_text("flask==2.0.0")
    (python_project / ".venv").mkdir()


    rust_project = tmp_path / "rust-app"
    rust_project.mkdir()
    (rust_project / "Cargo.toml").write_text('[package]\nname = "test"')


    (tmp_path / ".git").mkdir()

    return tmp_path

def test_scanner_init():
    scanner = DirectoryScanner(Path("/test"))
    assert scanner.root_path == Path("/test").resolve()
    assert scanner.max_depth == -1


def test_scan_complete(test_project_structure):
    result = scan_directory(test_project_structure)

    assert result.total_projects == 3  # Node, Python, Rust
    assert result.directories_scanned > 0
    assert len(result.errors) == 0

    project_types = [p.project_type for p in result.projects]
    assert ProjectType.NODE in project_types
    assert ProjectType.PYTHON in project_types
    assert ProjectType.RUST in project_types