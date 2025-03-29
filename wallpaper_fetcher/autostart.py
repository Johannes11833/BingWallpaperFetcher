from enum import Enum
from pathlib import Path
import platform
import subprocess
import sys
from typing import Iterable, List
from wallpaper_fetcher import APP_NAME
from wallpaper_fetcher.logger import log


class OperatingSystem(Enum):
    WINDOWS = "Windows"
    MAC = "Darwin"
    LINUX = "Linux"


def get_os() -> OperatingSystem:
    return OperatingSystem(platform.system())


OS = get_os()


# WINDOWS
WINDOWS_TASK_NAME = "BingWallpaperFetcherTask"

# LINUX
LINUX_AUTOSTART_DIR = Path.home() / ".config" / "autostart"
LINUX_LAUNCH_FILE_PATH = Path(LINUX_AUTOSTART_DIR, "wallpaper_fetcher.desktop")


def is_frozen() -> bool:
    if getattr(sys, "frozen", False):
        # we are running in a bundle
        return True
    return False


def get_launch_args() -> List[str]:
    launch_args = sys.argv.copy()

    # make sure the path of the first item (either source file or standalone executable) is absolute
    if launch_args:
        launch_args[0] = str(Path(launch_args[0]).absolute())

    # insert the path to the python executable in non-frozen mode
    # on windows if run using poetry, the first item in argv is a cmd file
    # so here we do not need to insert the executable either
    if not is_frozen() and Path(launch_args[0]).suffix == ".py":
        exe = Path(sys.executable)
        # check if pythonw is available
        python_w = Path(exe.parent, f"{exe.stem}w{exe.suffix}")
        if python_w.is_file():
            launch_args.insert(0, python_w)
        else:
            launch_args.insert(0, exe)

    return launch_args


def autostart_supported() -> bool:
    return OS in [OperatingSystem.WINDOWS, OperatingSystem.LINUX]


def set_auto_start(
    enable: bool, args: Iterable[str] = (), interval: int | None = None
) -> bool:
    launch_args = " ".join(f'"{a}"' for a in args)
    result = False
    if OS == OperatingSystem.WINDOWS:
        __manage_windows_task(launch_args, enable, interval)
    elif OS == OperatingSystem.LINUX:
        if LINUX_AUTOSTART_DIR.is_dir():
            if enable:
                desktop = f"[Desktop Entry]\nType=Application\nName={APP_NAME}\nExec={launch_args}"
                log.debug(
                    f'Writing desktop-file to "{LINUX_LAUNCH_FILE_PATH}" with content:\n {desktop}'
                )
                LINUX_LAUNCH_FILE_PATH.write_text(desktop)
                result = True
            else:
                LINUX_LAUNCH_FILE_PATH.unlink()
                result = True
        else:
            log.warning(
                f"Autostart folder {LINUX_AUTOSTART_DIR} does not exist. Autostart  was not enabled."
            )

    else:
        log.warning(f"Autostart not supported for {OS}.")

    return result


def get_autostart_enabled() -> bool:
    if OS == OperatingSystem.WINDOWS:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", WINDOWS_TASK_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0

    elif OS == OperatingSystem.LINUX:
        return LINUX_LAUNCH_FILE_PATH.is_file()
    else:
        log.warning(f"{OS} is not supported (get_autostart_enabled)")
        return False


# ---------------------------------- WINDOWS --------------------------------- #


def __manage_windows_task(args: str, enable: bool, interval_minutes: int | None = None):

    if enable:
        if interval_minutes is None:
            interval_minutes = 60

        command = [
            "schtasks",
            "/Create",
            "/TN",
            WINDOWS_TASK_NAME,
            "/TR",
            args,
            "/SC",
            "MINUTE",
            "/MO",  # Modifier
            str(interval_minutes),
            "/F",
        ]
    elif get_autostart_enabled():
        command = [
            "schtasks",
            "/Delete",
            "/TN",
            WINDOWS_TASK_NAME,
            "/F",  # Force delete without asking for confirmation
        ]
    else:
        return

    log.debug(f"Running shell command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

    # Check if it succeeded
    if result.returncode == 0:
        log.debug("Task config succeeded!")
    else:
        log.error("Task config succeeded failed!")
        log.error(
            f"Return Code: { result.returncode}",
        )
        log.error(f"STDOUT: {result.stdout}")
        log.error(f"STDERR: {result.stderr}")
