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
    return f"{size_bytes:.1f} {unit}"