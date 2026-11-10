"""
Asset path resolution for development and PyInstaller builds.

Works in both:
  - normal Python execution (files on disk)
  - PyInstaller one-dir or one-file builds (sys._MEIPASS)
"""

import sys
import os


def assets_path(relative: str) -> str:
    """
    Return the absolute path to an asset inside data/assets/.

    Parameters
    ----------
    relative : str
        Path relative to data/assets/ (e.g. "icons/book.svg").

    Returns
    -------
    str
        Absolute path that works in dev and frozen builds.
    """
    # In PyInstaller: data/ is extracted to _MEIPASS/data/
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", sys.executable)
        return os.path.join(base, "data", "assets", relative)

    # Normal dev: the project root is the parent of ui/
    current_dir = os.path.dirname(os.path.abspath(__file__))  # ui/
    project_root = os.path.dirname(current_dir)  # project root
    return os.path.join(project_root, "data", "assets", relative)


def data_path(relative: str) -> str:
    """
    Return absolute path to a file inside data/ (non-asset files).

    Useful for config.json, glossary.db, translated/, etc.
    Works in dev and frozen builds.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", sys.executable)
        return os.path.join(base, "data", relative)

    current_dir = os.path.dirname(os.path.abspath(__file__))  # ui/
    project_root = os.path.dirname(current_dir)  # project root
    return os.path.join(project_root, "data", relative)


def core_dir() -> str:
    """Return the absolute path to the core/ directory."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", sys.executable)
        return os.path.join(base, "core")
    current_dir = os.path.dirname(os.path.abspath(__file__))  # ui/
    project_root = os.path.dirname(current_dir)  # project root
    return os.path.join(project_root, "core")


def project_root() -> str:
    """Return the absolute path to the project root (parent of ui/ and core/).
    
    Works in both development and PyInstaller builds.
    Use this instead of manually computing os.path.dirname(os.path.abspath(...)) everywhere.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", sys.executable)
        # In PyInstaller: project files are at _MEIPASS/ level
        return base
    
    current_dir = os.path.dirname(os.path.abspath(__file__))  # ui/
    return os.path.dirname(current_dir)  # project root


def data_dir() -> str:
    """Return the absolute path to the data/ directory."""
    return os.path.join(project_root(), "data")


def assets_dir() -> str:
    """Return the absolute path to the data/assets/ directory."""
    return os.path.join(data_dir(), "assets")
