"""
    Detector Test
"""

import pytest
from pathlib import Path


from scythe.detector import ArtifactDetector, detect_artifacts, ARTIFACT_PATTERNS
from scythe.models import ProjectType

@pytest.fixture
def node_project_with_artifact(tmp_path):

    project = tmp_path / "my-app"
    project.mkdir()

    node_modules = project / "node_modules"
    node_modules.mkdir()
    (node_modules / "express").mkdir()
    (node_modules / "express" / "index.js").write_text('modules.exports = {}')

    dist = project / "dist"
    dist.mkdir()
    (dist / "bundle.js").write_text("Console.log('bundle')")

    (project / "src").mkdir()
    (project / "src" / "index.js").write_text("console.log('hello')")

    return project


@pytest.fixture
def python_project_with_artifacts(tmp_path):
    project = tmp_path / "my-python-app"
    project.mkdir()

    (project / "requirements.txt").write_text("flask==2.0.0")

    venv = project / ".venv"
    venv.mkdir()
    (venv / "lib").mkdir()

    pycache = project / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-310.pyc").write_bytes(b'\x00\x01\x02')

    (project / "main.py").write_text("print('hello')")

    return project


def test_artifact_pattern():
    assert ProjectType.NODE in ARTIFACT_PATTERNS
    assert ProjectType.PYTHON in ARTIFACT_PATTERNS
    assert ProjectType.RUST in ARTIFACT_PATTERNS

    assert len(ARTIFACT_PATTERNS[ProjectType.NODE]) > 0
    assert 'node_modules' in ARTIFACT_PATTERNS[ProjectType.NODE]

def test_get_artifacts_patterns():
    detector = ArtifactDetector(Path("/test"), ProjectType.PYTHON)
    patterns = detector.get_artifact_pattern()

    assert '.venv' in patterns
    assert '__pycache__' in patterns


def test_is_artifact_node() :
    detector = ArtifactDetector(Path("/test"), ProjectType.NODE)

    assert detector.is_artifact(Path("/test/node_modules")) == True
    assert detector.is_artifact(Path("/test/dist")) == True
    assert detector.is_artifact(Path("/test/src")) == False


def test_is_artifact_python() :
    detector = ArtifactDetector(Path("/test"), ProjectType.PYTHON)

    assert detector.is_artifact(Path("/test/.venv")) == True
    assert detector.is_artifact(Path("/test/__pycache__")) == True
    assert detector.is_artifact(Path("/test/main.py")) == False


def test_detect_artifacts_node(node_project_with_artifacts):
    artifacts = detect_artifacts(node_project_with_artifacts, ProjectType.NODE)
    assert len(artifacts) >= 2

    artifact_names = {a.artifact_type for a in artifacts}
    assert 'node_modules' in artifact_names
    assert 'dist' in artifact_names


    for artifact in artifacts:
        assert artifact.size_bytes > 0
        assert artifact.last_modified is not None


def test_detect_artifacts_python(python_project_with_artifacts):
    artifacts = detect_artifacts(python_project_with_artifacts, ProjectType.PYTHON)
    assert len(artifacts) >= 2

    artifact_names = {a.artifact_type for a in artifacts}
    assert '.venv' in artifact_names
    assert '__pycache__' in artifact_names