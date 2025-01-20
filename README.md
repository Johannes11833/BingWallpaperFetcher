[![PyPI - Version](https://img.shields.io/pypi/v/wallpaper-fetcher?logo=PyPI)](https://pypi.org/project/wallpaper-fetcher/)

# Wallpaper Fetcher
Small cli program to automatically download and set the daily Bing wallpaper on Windows, Linux or Mac.


```console
> wallpaper-fetcher -h  

usage: Wallpaper Fetcher [-h] [-f] [-n NUMBER] [-r RES] [-d] [-l LOCALE] [-o OUTPUT] [-v] [--debug]

This little tool fetches the Bing wallpaper of the day and automatically applies it (Windows/Mac/Linux).

options:
  -h, --help           show this help message and exit
  -f, --force          force re-download a already downloaded image. (default: False)
  -n, --number NUMBER  number of latest wallpapers to download. (default: 1)
  -r, --res RES        Custom resolution. UHD by default. (default: UHD)
  -d, --download       Only download the wallpaper(s) without updating the desktop background. (default: False)
  -l, --locale LOCALE  The market to use. (default: en-US)
  -o, --output OUTPUT  Output directory where the wallpapers should be saved. (default: None)
  -v, --version        Prints the installed version number. (default: False)
  --debug              Set log level to debug. (default: False)
```

In addition, the [executable](https://github.com/Johannes11833/BingWallpaperFetcher/releases) versions of this program support enabling autostart which automatically downloads the current wallpaper of the day on login.
To enable autostart, use `--enable-auto` and to disable it use `--disable-auto`.


## Credits
- The source code in [set_wallpaper.py](wallpaper_fetcher/set_wallpaper.py) was copied from the [Textual Paint](https://github.com/1j01/textual-paint) project licensed under the [MIT License](https://github.com/1j01/textual-paint?tab=MIT-1-ov-file).
