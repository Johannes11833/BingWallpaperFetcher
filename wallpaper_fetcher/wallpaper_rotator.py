import os
import random
import signal
import sys
import time

from wallpaper_fetcher import DATA_DIR, PID_FILE
from wallpaper_fetcher.autostart import OperatingSystem, get_os
from wallpaper_fetcher.logger import log
from wallpaper_fetcher.set_wallpaper import set_wallpaper


def stop_running_instance() -> bool:
    success = False
    if PID_FILE.is_file():
        pid_running = int(PID_FILE.read_text())
        try:
            # kill the running instance
            # (might fail if it is not running but .pid file exists)
            os.kill(
                pid_running,
                (
                    signal.SIGTERM
                    if get_os() == OperatingSystem.WINDOWS
                    else signal.SIGKILL
                ),
            )
            success = True
        except OSError:
            log.warning("Failed to kill running instance!")

        # remove old pid file
        PID_FILE.unlink(missing_ok=True)

        return success


def launch(update_interval: int):
    stop_running_instance()

    pid_current = os.getpid()
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid_current))

    rotate_wallpapers(update_interval)


def rotate_wallpapers(update_interval: int):
    paths = [
        file for file in DATA_DIR.iterdir() if file.is_file() and file.suffix == ".jpg"
    ]
    random.shuffle(paths)

    log.debug(f'{len(paths)} wallpapers were found in "{DATA_DIR}"')

    try:
        while True:
            for path in paths:
                if set_wallpaper(path):
                    log.info(f"Successfully updated the wallpaper to {path}")
                else:
                    log.error("Failed to set the wallpaper as background.")

                time.sleep(update_interval)
    except KeyboardInterrupt:
        log.debug("Removing pid file on exit.")
        PID_FILE.unlink(missing_ok=True)
        sys.exit()
