import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests

from bingwallpaper import VERSION
from bingwallpaper.set_wallpaper import set_wallpaper
from bingwallpaper.autostart import (
    autostart_supported,
    get_autostart_enabled,
    set_auto_start,
)
from bingwallpaper.logger import log


data_dir = Path.home() / "Documents" / "BingWallpapers"
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


def fetch_wallpaper_metadata(
    locale: str | None = None,
    n: int = 1,
) -> Optional[List[WallPaper]]:
    if locale is None:
        locale = "en-US"
    url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n={n}&mkt={locale}"
    log.debug(f"Fetching Bing wallpaper metadata from {url}")

    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.content:
        content = response.json().get("images", None)
        log.debug(f"Received Bing wallpaper metadata:\n{content}")

        if content:
            return [WallPaper.from_json(child) for child in content]
        else:
            log.error("Failed to get metadata for latest Bing wallpaper(s)!")


def download_wallpapers(
    n: int = 1,
    locale: str = "en-US",
    resolution: str | None = None,
    force: bool = False,
) -> List[WallPaper]:
    data_dir.mkdir(exist_ok=True, parents=True)

    walls = fetch_wallpaper_metadata(locale, n=n)
    downloads = 0

    if not walls:
        log.error("Failed to get metadata!")
        return None

    for wallpaper in walls:
        path = (
            data_dir
            / f"{wallpaper.startdate}_{wallpaper.title}.jpg".replace(" ", "_").lower()
        )
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
        log.info(f'Downloaded {downloads} new wallpaper(s) to "{data_dir}"')

    return walls


def get_current_wallpaper_locally(data_dir: Path) -> Optional[Path]:
    if not data_dir.is_dir():
        return False

    for file in data_dir.iterdir():
        if (
            file.is_file()
            and file.suffix == ".jpg"
            and file.name.startswith(str(datetime.today().strftime("%Y%m%d")))
        ):
            return file

    return None


def set_latest_wallpaper(
    resolution: str | None = None,
    locale: str | None = None,
):
    path = get_current_wallpaper_locally(data_dir=data_dir)
    if path:
        json_path = path.with_suffix(".json")
        walls = [WallPaper.from_json(json.loads(json_path.read_text()), path=path)]
        log.debug(f'Found latest wallpaper locally at "{path}"')
    else:
        walls = download_wallpapers(
            n=1,
            locale=locale,
            resolution=resolution,
        )

    if walls and walls[0].path:
        set_wallpaper(walls[0].path)
        log.info(f"Successfully updated the wallpaper to {walls[0].pretty_print()}")


def cli():
    parser = argparse.ArgumentParser(
        prog="BingWallpaper Fetcher",
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
        "-d",
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
        global data_dir
        data_dir = Path(args.output)

    if args.number > 1 or args.force:
        download_wallpapers(
            n=args.number,
            force=args.force,
            resolution=args.res,
        )

    set_latest_wallpaper(
        resolution=args.res,
        locale=args.locale,
    )


if __name__ == "__main__":
    cli()
