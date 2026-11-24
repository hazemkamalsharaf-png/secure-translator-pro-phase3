
import sys
import os
from ui.main_window import MainWindow
from ui.theme import ThemeManager, sync_appearance
from ui.asset_path import data_dir
from data.config import ConfigManager


def _ensure_data_dirs():
    """Create required data directories if they don't exist."""
    base = data_dir()
    for subdir in ("translated", "archived", "assets", "assets/icons", "assets/fonts"):
        os.makedirs(os.path.join(base, subdir), exist_ok=True)


def main():
    # Robust path resolution using __file__ instead of os.getcwd()
    current_dir = os.path.dirname(os.path.abspath(__file__)) # project root
    config_path = os.path.join(current_dir, "data", "config.json")

    # Ensure all required directories exist
    _ensure_data_dirs()

    # Load config and apply saved theme mode
    config = ConfigManager(config_path)
    theme_mode = config.get("theme_mode") or "dark"
    ThemeManager.get_instance().set_mode(theme_mode)
    sync_appearance(theme_mode)

    app = MainWindow(config_manager=config)
    app.mainloop()

if __name__ == "__main__":
    sys.exit(main())
