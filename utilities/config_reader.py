"""
utilities/config_reader.py

This module provides a simple function to read values from config/config.ini.
"""

# Import configparser to read INI files.
import configparser

# Import os to build the config file path reliably on any OS.
import os


# This function reads a value from config/config.ini for a given section and key.
def read_config(section: str, key: str) -> str:
    # Create a new ConfigParser object that understands INI format.
    parser = configparser.ConfigParser()

    # Build the absolute path to the project root (one folder above utilities/).
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Build the path to config/config.ini inside the project.
    config_path = os.path.join(project_root, "config", "config.ini")

    # Read the INI file from disk.
    parser.read(config_path)

    # Use try/except so we can raise a clear error if section/key is missing.
    try:
        # If the section does not exist, raise a KeyError with a friendly message.
        if not parser.has_section(section):
            raise KeyError(f"Section '{section}' not found in {config_path}")

        # If the key does not exist inside the section, raise a KeyError with a friendly message.
        if not parser.has_option(section, key):
            raise KeyError(f"Key '{key}' not found in section '{section}' in {config_path}")

        # Read the value as a string and return it.
        return parser.get(section, key)

    except Exception as e:
        # Re-raise the error as a RuntimeError so the test output is easy to understand.
        raise RuntimeError(f"Unable to read config value for [{section}] {key}. Error: {e}") from e

