"""
Bannière et éléments visuels pour Artifact-Scythe
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

BANNER = """
   ____            __  __       
  / __/____  ___  / /_/ /  ___  
 _\ \/ __/ |/ / |/ / / _ \/ -_) 
/___/\__/|___/|___/_/_//_/\__/  

Build Artifact Cleaner"""



VERSION = "0.3.0"


def display_banner(show_version: bool = True):
    banner_text = BANNER
    if show_version:
        banner_text += f" v{VERSION}"

    console.print(
        Panel(
            Text(banner_text, style="bold cyan", justify="center"),
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2)
        )
    )







