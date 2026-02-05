"""
Logger for artifacts
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler



def setup_logger(name: str = "scythe", level: int = logging.INFO, log_file: bool = True ) :
    """
    Setup logger
    Args :
        -name : name of the logger
        -level : logging level
        -log_file : Write a log to file
    return: A configured logger object
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_filename = log_dir / f"scyth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt= "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        logger.info(f"Log file created: {log_filename}")

    return logger

def get_logger(name: str = "scythe"):
    return logging.getLogger(name)