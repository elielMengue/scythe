"""
Cleaner of Artifacts
"""

import shutil
import time
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

from scythe.models.models import Project, ArtifactInfo, CleanResult

