"""
logging_config.py
-------------------
Central logging setup. Import get_logger(__name__) in any module
instead of using print() so errors are traceable in production.
"""

import logging
import sys

from config import LOG_LEVEL

_CONFIGURED = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger("resumeiq")
    root.setLevel(LOG_LEVEL)
    root.addHandler(handler)
    root.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root_logger()
    return logging.getLogger(f"resumeiq.{name}")
