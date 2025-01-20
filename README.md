![PyPI - Version](https://img.shields.io/pypi/v/wallpaper-fetcher?link=https%3A%2F%2Fpypi.org%2Fproject%2Fwallpaper-fetcher%2F)

# Wallpaper Fetcher
Small cli program to automatically download and set the daily Bing wallpaper on Windows, Linux or Mac.


```console
> wallpaper-fetcher -h  

usage: Wallpaper Fetcher [-h] [-f] [-n NUMBER] [-r RES] [-l LOCALE] [-d] [-o OUTPUT]

This neat little tool fetches the Bing wallpaper of the day and automatically applies it (Windows/Mac/Linux).

options:
  -h, --help           show this help message and exit
  -f, --force          force re-download a already downloaded image. (default: False)
  -n, --number NUMBER  number of latest wallpapers to download. (default: 1)
  -r, --res RES        Custom resolution. UHD by default. (default: UHD)
  -l, --locale LOCALE  The market to use. (default: en-US)
  -d, --debug          Set log level to debug. (default: False)
  -o, --output OUTPUT  Output directory where the wallpapers should be saved. (default: None)
```

## Credits
- The source code in [set_wallpaper.py](wallpaper_fetcher/set_wallpaper.py) was copied from the [Textual Paint](https://github.com/1j01/textual-paint) project licensed under the [MIT License](https://github.com/1j01/textual-paint?tab=MIT-1-ov-file).
