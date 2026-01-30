"""
    Utils functions
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Set

IGNORED_PATTERNS: Set[str] = {
    '.git',
    '.svn',
    '.hg',
    '.bzr',
    '__MACOSX',
    '.DS_Store',
    'Thumbs.db',
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    '*~'
}

def format_size(size_bytes: int) -> str:
    if size_bytes < 0 :
        raise ValueError("Size must be positive")

    for unit in ['B','KB','MB','GB', 'TB']:
        if size_bytes < 1024.0 :
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def calculate_directory_size(path: Path, follow_symlinks: bool = False) -> int:
    if not path.exists():
        raise ValueError("The path does not exist")
    if not path.is_dir():
        raise ValueError("Path is not a directory")

    total_size = 0

    try:
        for entry in path.rglob('*'):
            if entry.is_symlink() and not follow_symlinks:
                continue
            if entry.is_file():
                try:
                    total_size+= entry.stat().st_size
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass

    return total_size


def is_ignored_path(path: Path, custom_ignores: Set[str] = None) -> bool :
    ignored = IGNORED_PATTERNS.copy()
    if custom_ignores:
        ignored.update(custom_ignores)

    if path.name in ignored:
        return True

    for pattern in ignored:
        if '*' in pattern :
            pattern_clean = pattern.replace('*', '')
            if pattern_clean in path.name :
                return True
    return False