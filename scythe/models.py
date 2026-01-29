"""
    Data Structure
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

class ProjectType(Enum) :
    """
        SUPPORTED PROJECT TYPES
    """

    NODE = "node"
    PYTHON = "python"
    RUST = "rust"
    JAVA_MAVEN = "java_maven"
    JAVA_GRADLE = "java_gradle"
    GO = "go"
    RUBY = "ruby"
    DOTNET = "dotnet"
    UNKNOWN = "unknown"

    def __str__(self):
        return self.value

    @property
    def display_name(self):
        names = {
            ProjectType.NODE : "Node.js",
            ProjectType.PYTHON : "Python",
            ProjectType.RUST : "Rust",
            ProjectType.JAVA_MAVEN : "Java (Maven)",
            ProjectType.JAVA_GRADLE : "Java (Gradle)",
            ProjectType.GO : "Go",
            ProjectType.RUBY : "Ruby",
            ProjectType.DOTNET : ".NET",
            ProjectType.UNKNOWN : "Unknown"
        }

        return names.get(self, self.value)

@dataclass
class ArtifactInfo :
        """
            Information about the artifacts
        """

        path: Path
        size_bytes: int
        last_modified: datetime
        artifact_type: str

        @property
        def size_formatted(self) -> str :
            from scythe.utils import format_size
            return format_size(self.size_bytes)


@dataclass
class Project:
        path: Path
        project_types: ProjectType
        marker_files: List[str] = field(default_factory=list)
        artifacts: List[ArtifactInfo] = field(default_factory=list)
        total_artifact_size: int = 0
        last_scanned: datetime = field(default_factory=datetime)

        def __post_init__(self) :
            self.total_artifact_size = sum(a.size_bytes for a in  self.artifacts)

        @property
        def total_size_formatted(self):
            from scythe.utils import format_size
            return format_size(self.total_artifact_size)

        @property
        def artifact_count(self):
            return len(self.artifacts)
