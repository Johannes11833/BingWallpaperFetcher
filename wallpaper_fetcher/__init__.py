from importlib import metadata
from pathlib import Path


VERSION = f'v{metadata.version("wallpaper_fetcher")}'
APP_NAME = "Wallpaper Fetcher"
DATA_DIR = Path.home() / "Pictures" / "Wallpapers"
PID_FILE = DATA_DIR / ".pid_file"
