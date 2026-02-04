"""
    Utility to format report
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from scythe.models import ScanResult, Project


def format_to_json(result: ScanResult, pretty: bool = True) -> str:
    data = {
        "scan_date": result.scan_date.isoformat(),
        "root_path": str(result.root_path),
        "scan_duration": result.scan_duration,
        "statistics": {
            "directories_scanned": result.directories_scanned,
            "files_scanned": result.files_scanned,
            "total_projects": result.total_projects,
            "total_artifacts": sum(p.artifact_count for p in result.projects),
            "total_size_bytes": result.total_artifact_size,
            "total_size_formatted": result.total_size_formatted
        },
        "projects": [
            {
                "path": str(project.path),
                "type": project.project_type.value,
                "type_display": project.project_type.display_name,
                "marker_files": project.marker_files,
                "artifacts": [
                    {
                        "type": artifact.artifact_type,
                        "path": str(artifact.path),
                        "size_bytes": artifact.size_bytes,
                        "size_formatted": artifact.size_formatted,
                        "last_modified": artifact.last_modified.isoformat()
                    }
                    for artifact in project.artifacts
                ],
                "total_artifact_size": project.total_artifact_size,
                "total_size_formatted": project.total_size_formatted
            }
            for project in result.projects
        ],
        "errors": result.errors
    }

    if pretty :
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def format_to_csv(result: ScanResult) -> str:

    lines = ["Type,Path,Artifacts,Size (bytes),Size"]

    for project in result.projects:
        lines.append(
            f"{project.project_type.value},"
            f"{project.path},"
            f"{project.artifact_count},"
            f"{project.total_artifact_size},"
            f"{project.total_size_formatted}"
        )

    return "\n".join(lines)


def save_report(
        result: ScanResult,
        output_path: Path,
        format: str = "json"
)  -> None:

    if format == "json":
        content = format_to_json(result)
    elif format == "csv":
        content = format_to_csv(result)
    else:
        raise ValueError(f"Format non supporté: {format}")

    output_path.write_text(content, encoding='utf-8')

