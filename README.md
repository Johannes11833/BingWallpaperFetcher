# Bing Wallpaper Fetcher
Small cli program to automatically download and set the daily Bing wallpaper on Windows, Linux or Mac.


```console
 python .\bing.py -h  
                            
usage: BingWallpaper Fetcher [-h] [-f] [-n NUMBER] [-r RESOLUTION] [-l LOCALE] [-d] [-o OUTPUT]

This neat little tool fetches the Bing wallpaper of the day and automatically applies it (Windows/Mac/Linux).

options:
  -h, --help            show this help message and exit
  -f, --force           force re-download a already downloaded image. (default: False)
  -n, --number NUMBER   number of latest wallpapers to download. (default: 1)
  -r, --resolution RESOLUTION
                        Custom resolution. UHD by default. (default: UHD)
  -l, --locale LOCALE   The market to use. (default: en-US)
  -d, --debug           Set log level to debug. (default: False)
  -o, --output OUTPUT   Output directory where the wallpapers should be saved. (default: None)
```