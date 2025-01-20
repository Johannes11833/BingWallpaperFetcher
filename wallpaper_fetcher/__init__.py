from importlib.metadata import version
from pathlib import Path


VERSION = f'v{version("wallpaper_fetcher")}'
APP_NAME = "Wallpaper Fetcher"
DATA_DIR = Path.home() / "Documents" / "BingWallpapers"
