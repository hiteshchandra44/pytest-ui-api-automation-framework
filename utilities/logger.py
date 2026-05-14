"""
utilities/logger.py

This module provides a simple logger factory function.
It writes logs to both the console and a dated file in the logs/ folder.
"""

# Import Python's built-in logging module (no third-party logging libraries).
import logging

# Import date utilities to build the log filename with today's date.
from datetime import date

# Import os for path handling and creating the logs folder if needed.
import os


# This function creates and returns a configured logger for the given name.
def get_logger(name: str) -> logging.Logger:
    # Get (or create) a logger with the provided name.
    logger = logging.getLogger(name)

    # Set the minimum level for this logger (INFO is a good default for beginners).
    logger.setLevel(logging.INFO)

    # Prevent logs from being duplicated if the root logger is also configured elsewhere.
    logger.propagate = False

    # If the logger already has handlers, return it as-is to avoid duplicate messages.
    if logger.handlers:
        return logger

    # Build the absolute path to the project root (one folder above utilities/).
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Build the logs folder path inside the project.
    logs_dir = os.path.join(project_root, "logs")

    # Create the logs folder if it does not exist.
    os.makedirs(logs_dir, exist_ok=True)

    # Create today's date string in the format YYYY-MM-DD.
    today = date.today().isoformat()

    # Build the log file path (example: logs/test_2026-05-07.log).
    log_file_path = os.path.join(logs_dir, f"test_{today}.log")

    # Define the required log format:
    # [timestamp] [level] [filename] - message
    log_format = "[%(asctime)s] [%(levelname)s] [%(filename)s] - %(message)s"

    # Create a formatter using the format above.
    formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Create a console handler to print logs to the terminal.
    console_handler = logging.StreamHandler()

    # Set the formatter on the console handler.
    console_handler.setFormatter(formatter)

    # Create a file handler to write logs to the dated log file.
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")

    # Set the formatter on the file handler.
    file_handler.setFormatter(formatter)

    # Add both handlers to the logger so it logs to console + file.
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Return the configured logger.
    return logger

