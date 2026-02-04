"""
    Utility to format report
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from scythe.models import ScanResult, Project


def format_to_json(result: ScanResult, pretty: bool = True) -> str:
