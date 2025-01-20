import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Dict, List, Optional
import requests

from wallpaper_fetcher import VERSION, DATA_DIR
from wallpaper_fetcher.set_wallpaper import set_wallpaper
from wallpaper_fetcher.autostart import (
    autostart_supported,
    get_autostart_enabled,
    set_auto_start,
)
from wallpaper_fetcher.logger import log


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}


class WallPaper:
    def __init__(
        self,
        title: str,
        url: str,
        startdate: int,
        enddate: int,
        copyright: str,
        raw: dict,
        path: Path | None,
    ):
        self.title = title
        self.url = url
        self.startdate = startdate
        self.enddate = enddate
        self.copyright = copyright
        self.raw = raw
        self.path = path

    @classmethod
    def from_json(cls, content: Dict, path: Path | None = None):
        return cls(
            title=content["title"],
            # content["url"] holds the rest of the url
            url="https://bing.com" + content["url"],
            startdate=content["startdate"],
            enddate=content["enddate"],
            copyright=content["copyright"],
            raw=content,
            path=path,
        )

    def pretty_print(self) -> str:
        return f'Wallpaper(title: "{self.title}", copyright: "{self.copyright}", startdate: {self.startdate}, path: "{self.path}")'

    def __repr__(self):
        return self.pretty_print()


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
        response = requests.get(url, headers=headers)
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
        path = (
            DATA_DIR
            / f"{wallpaper.startdate}_{wallpaper.title}".replace(" ", "_")
            .replace("'", "")
            .replace('"', "")
            .replace("!", "")
            .replace(".", "")
            .replace(",", "")
            .lower()
        ).with_suffix(".jpg")
        url = wallpaper.url

        if path.is_file() and not force:
            wallpaper.path = path
            log.debug(f"{wallpaper.pretty_print()} found so skipping its download.")
            continue

        if resolution:
            url = url.replace("_1920x1080", "_" + resolution)

        log.debug(f"Downloading wallpaper from {url}")

        response = requests.get(url, headers=headers)

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
        help="force re-download a already downloaded image.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-n",
        "--number",
        help=f"number of latest wallpapers to download.",
        default=1,
        type=int,
    )

    parser.add_argument(
        "-r",
        "--res",
        help="Custom resolution. UHD by default.",
        type=str,
        default="UHD",
    )

    parser.add_argument(
        "-d",
        "--download",
        help="Only download the wallpaper(s) without updating the desktop background.",
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
        help="Output directory where the wallpapers should be saved.",
        default=None,
    )

    if autostart_supported():
        # only add autostart options if this is the frozen executable
        parser.add_argument(
            "--enable-auto",
            help="Enable autostart.",
            action="store_true",
            default=False,
        )

        parser.add_argument(
            "--disable-auto",
            help="Remove autostart.",
            action="store_true",
            default=False,
        )

    parser.add_argument(
        "-v",
        "--version",
        help="Prints the installed version number.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--debug",
        help="Set log level to debug.",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    if args.version:
        print(VERSION)
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

    walls = download_wallpapers(
        n=args.number,
        force=args.force,
        resolution=args.res,
    )

    if not args.download and walls:
        set_latest_wallpaper(
            wallpaper=walls[0],
        )


if __name__ == "__main__":
    cli()
