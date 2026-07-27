import logging
import sys


def setup_logger(name: str = "omni", level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a structured logger instance for OMNI Digital Twin.
    Ensures consistent log formatting across Authentication, Resume, GitHub, Career, ATS, and AI layers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Retrieves a named structured logger under the OMNI namespace."""
    return setup_logger(f"omni.{name}")
