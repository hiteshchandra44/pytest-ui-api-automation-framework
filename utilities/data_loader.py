"""
utilities/data_loader.py

Small helper to load test data JSON files from the project-level testdata/ folder.
This is additive and does not modify any existing tests.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from utilities.logger import get_logger


logger = get_logger(__name__)


def load_test_data(filename: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file from the repository's testdata/ directory.

    Args:
        filename: JSON filename (e.g. "ui_test_data.json")

    Returns:
        Parsed JSON as a dict.

    Raises:
        FileNotFoundError: if the file does not exist under testdata/
        ValueError: if the JSON is invalid or not a JSON object
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(project_root, "testdata", filename)

    logger.info(f"Loading test data: {data_path}")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Test data file not found: '{filename}'. Expected at: {data_path}"
        ) from e

    if not isinstance(data, dict):
        raise ValueError(f"Test data file must contain a JSON object at top-level: {data_path}")

    return data

