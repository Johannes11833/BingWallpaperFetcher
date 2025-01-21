[![PyPI - Version](https://img.shields.io/pypi/v/wallpaper-fetcher?logo=PyPI)](https://pypi.org/project/wallpaper-fetcher/)

# Wallpaper Fetcher
Small cli program to automatically download and set the daily Bing wallpaper on Windows, Linux or Mac.


```console
> wallpaper-fetcher -h  

usage: Wallpaper Fetcher [-h] [-f] [-n NUMBER] [-r RES] [-d] [-l LOCALE] [-o OUTPUT] [-v] [--debug]

This little tool fetches the Bing wallpaper of the day and automatically applies it (Windows/Mac/Linux).

options:
  -h, --help            show this help message and exit
  -f, --force           Force re-download an already downloaded image (default: False)
  -n, --number NUMBER   Number of latest wallpapers to download (default: 1)
  -r, --res RES         Custom resolution. UHD by default. Use --valid-res to see all valid resolutions (default: UHD)
  -d, --download        Only download the wallpaper(s) without updating the desktop background (default: False)
  -l, --locale LOCALE   The market to use. (default: en-US)
  -o, --output OUTPUT   Output directory where the wallpapers should be saved (default: None)
  -u, --update          Automatically update the wallpaper every x seconds (default: False)
  -i, --update-interval UPDATE_INTERVAL
                        The interval in seconds to use to update the wallpaper (default: 300)
  -a, --attached        Run wallpaper rotation in attached mode (see all logs) (default: False)
  -s, --stop            Stop the wallpaper rotator (default: False)
  -v, --version         Prints the installed version number (default: False)
  --valid-res           List all valid resolutions (default: False)
  --debug               Set log level to debug (default: False)
```

In addition, the [executable](https://github.com/Johannes11833/BingWallpaperFetcher/releases) versions of this program support enabling autostart which automatically downloads the current wallpaper of the day on login.
To enable autostart, use `--enable-auto` and to disable it use `--disable-auto`:

```
  --enable-auto         Enable autostart (default: False)
  --disable-auto        Remove autostart (default: False)
```


## Credits
- The source code in [set_wallpaper.py](wallpaper_fetcher/set_wallpaper.py) was copied from the [Textual Paint](https://github.com/1j01/textual-paint) project licensed under the [MIT License](https://github.com/1j01/textual-paint?tab=MIT-1-ov-file).
