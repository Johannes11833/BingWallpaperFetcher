import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import List, Optional
import requests

from wallpaper_fetcher import VERSION, DATA_DIR, wallpaper_rotator
from wallpaper_fetcher.set_wallpaper import set_wallpaper
from wallpaper_fetcher.autostart import (
    autostart_supported,
    get_autostart_enabled,
    is_frozen,
    set_auto_start,
)
from wallpaper_fetcher.logger import log
from wallpaper_fetcher.wallpaper import WallPaper


# list according to https://github.com/TimothyYe/bing-wallpaper
VALID_RESOLUTIONS = [
    "UHD",
    "1920x1200",
    "1920x1080",
    "1366x768",
    "1280x768",
    "1024x768",
    "800x600",
    "800x480",
    "768x1280",
    "720x1280",
    "640x480",
    "480x800",
    "400x240",
    "320x240",
    "240x320",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}


def fetch_wallpaper_metadata(
    locale: str | None = None,
    n: int = 1,
) -> Optional[List[WallPaper]]:
    if locale is None:
        locale = "en-US"
    url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n={n}&mkt={locale}"
    log.debug(f"Fetching Bing wallpaper metadata from {url}")
    retry_counter = 1

    while retry_counter <= 5:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200 and response.content:
            content = response.json().get("images", None)
            log.debug(f"Received Bing wallpaper metadata:\n{content}")

            if content:
                return [WallPaper.from_json(child) for child in content]

        log.warning(f"Failed to get metadata (retry={retry_counter})")
        time.sleep(1)
        retry_counter += 1


def download_wallpapers(
    n: int = 1,
    locale: str = "en-US",
    resolution: str | None = None,
    force: bool = False,
) -> List[WallPaper]:
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    if n == 1 and not force:
        path = get_current_wallpaper_locally(DATA_DIR=DATA_DIR)
        if path:
            json_path = path.with_suffix(".json")
            walls = [WallPaper.from_json(json.loads(json_path.read_text()), path=path)]
            log.debug(f'Found latest wallpaper locally at "{path}"')
            return walls

    walls = fetch_wallpaper_metadata(locale, n=n)
    downloads = 0

    if not walls:
        log.error("Failed to get metadata!")
        return None

    for wallpaper in walls:
        file_name = f"{wallpaper.startdate}_{re.sub(r'[^a-zA-Z0-9 ]', '', wallpaper.title)}".replace(
            " ", "_"
        ).lower()
        path = (DATA_DIR / file_name).with_suffix(".jpg")
        url = wallpaper.url

        if path.is_file() and not force:
            wallpaper.path = path
            log.debug(f"{wallpaper.pretty_print()} found so skipping its download.")
            continue

        if resolution:
            url = url.replace("_1920x1080", "_" + resolution)

        log.debug(f"Downloading wallpaper from {url}")

        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            open(path, "wb").write(response.content)
            path.with_suffix(".json").write_text(
                json.dumps(wallpaper.raw, indent="\t"),
            )
            wallpaper.path = path
            downloads += 1
        else:
            log.error(f"Failed to download {wallpaper.pretty_print()}")

    if downloads > 0:
        log.info(f'Downloaded {downloads} new wallpaper(s) to "{DATA_DIR}"')

    # drop all wallpapers that failed to download
    return [w for w in walls if w.path]


def get_current_wallpaper_locally(DATA_DIR: Path) -> Optional[Path]:
    if not DATA_DIR.is_dir():
        return False

    for file in DATA_DIR.iterdir():
        if (
            file.is_file()
            and file.suffix == ".jpg"
            and file.name.startswith(str(datetime.today().strftime("%Y%m%d")))
        ):
            return file

    return None


def set_latest_wallpaper(
    wallpaper: WallPaper,
):
    if wallpaper and wallpaper.path:
        success = set_wallpaper(wallpaper.path)
        log.info(f"Successfully updated the wallpaper to {wallpaper.pretty_print()}")
        if not success:
            log.error("Failed to set the wallpaper as background.")


def cli():
    parser = argparse.ArgumentParser(
        prog="Wallpaper Fetcher",
        description="This little tool fetches the Bing wallpaper of the day and automatically applies it (Windows/Mac/Linux).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--force",
        help="Force re-download an already downloaded image",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-n",
        "--number",
        help=f"Number of latest wallpapers to download",
        default=1,
        type=int,
    )

    parser.add_argument(
        "-r",
        "--res",
        help="Custom resolution. UHD by default. Use --valid-res to see all valid resolutions",
        type=str,
        default="UHD",
    )

    parser.add_argument(
        "-d",
        "--download",
        help="Only download the wallpaper(s) without updating the desktop background",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-l",
        "--locale",
        help="The market to use.",
        type=str,
        default="en-US",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output directory where the wallpapers should be saved",
        default=None,
    )

    if autostart_supported():
        # only add autostart options if this is the frozen executable
        parser.add_argument(
            "--enable-auto",
            help="Enable autostart",
            action="store_true",
            default=False,
        )

        parser.add_argument(
            "--disable-auto",
            help="Remove autostart",
            action="store_true",
            default=False,
        )

    parser.add_argument(
        "-u",
        "--update",
        help="Automatically update the wallpaper every x seconds",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-i",
        "--update-interval",
        help="The interval in seconds to use to update the wallpaper",
        default=60 * 5,
        type=int,
    )

    parser.add_argument(
        "-a",
        "--attached",
        help="Run wallpaper rotation in attached mode (see all logs)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-s",
        "--stop",
        help="Stop the wallpaper rotator",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-v",
        "--version",
        help="Prints the installed version number",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--valid-res",
        help="List all valid resolutions",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--debug",
        help="Set log level to debug",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    if args.version:
        print(VERSION)
        return

    if args.valid_res:
        print(
            "The following are all the valid resolution options that you can use with --res:"
        )
        print(", ".join(VALID_RESOLUTIONS))
        return

    if args.debug:
        log.setLevel(logging.DEBUG)

    if autostart_supported():
        if args.enable_auto or args.disable_auto:
            set_auto_start(enable=args.enable_auto)
            print("Autostart " + ("ON" if get_autostart_enabled() else "OFF"))
            return

    if args.output:
        global DATA_DIR
        DATA_DIR = Path(args.output)

    if args.stop:
        if wallpaper_rotator.stop_running_instance():
            print("Running instance stopped.")
        return

    walls = download_wallpapers(
        n=args.number,
        force=args.force,
        resolution=args.res,
    )

    if args.update:
        if not args.attached:
            launch_args = sys.argv.copy()
            if not is_frozen():
                launch_args.insert(0, sys.executable)
            launch_args.append("--attached")
            log.debug(
                f"Rerunning in detached mode with the following args: {launch_args}"
            )
            subprocess.Popen(
                launch_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log.info(
                f"Wallpaper rotation was enabled with refresh interval set to {args.update_interval}s"
            )
            log.info(f'Use "--stop" to stop the wallpaper rotation.')
            return

        log.info(
            f"Wallpaper rotator is enabled with update_interval set to {args.update_interval}s."
        )
        wallpaper_rotator.launch(args.update_interval)
    elif not args.download:
        set_latest_wallpaper(
            wallpaper=walls[0] if walls else None,
        )
    else:
        log.debug("Background was not updated as --download mode is active.")


if __name__ == "__main__":
    cli()
