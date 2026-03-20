import os
from pathlib import Path


def get_project_root():
    """
    Returns project root directory
    """
    return Path(__file__).resolve().parents[3]


def get_processed_dir():
    """
    Returns data/processed directory path
    """
    root = get_project_root()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return processed