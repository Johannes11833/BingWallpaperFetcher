from enum import Enum
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Iterable, List, Tuple
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
WINDOWS_TASK_NAME_LOGON_TRIGGER = "BingWallpaperFetcher"
WINDOWS_TASK_NAME_MINUTES_TRIGGER = "BingWallpaperFetcher-PeriodicalTrigger"

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


def get_autostart_enabled(
    windows_task: Tuple[str] = (
        WINDOWS_TASK_NAME_LOGON_TRIGGER,
        WINDOWS_TASK_NAME_MINUTES_TRIGGER,
    ),
) -> bool:
    if OS == OperatingSystem.WINDOWS:
        enabled = False
        for task_name in windows_task:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", task_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if result.returncode == 0:
                enabled = True
                log.debug(f"Task '{task_name}': ON")
            else:
                log.debug(f"Task '{task_name}': OFF")
        return enabled

    elif OS == OperatingSystem.LINUX:
        return LINUX_LAUNCH_FILE_PATH.is_file()
    else:
        log.warning(f"{OS} is not supported (get_autostart_enabled)")
        return False


# ---------------------------------- WINDOWS --------------------------------- #


def __manage_windows_task(args: str, enable: bool, interval_minutes: int | None = None):

    if enable:
        command = [
            "schtasks",
            "/Create",
            "/TN",
            WINDOWS_TASK_NAME_LOGON_TRIGGER,
            "/TR",
            f"{args}",
            "/SC",
            "ONLOGON",
            "/RU",
            os.getlogin(),
            "/F",
        ]

        if interval_minutes is not None:
            # also create a minutes trigger
            command.extend(
                [
                    "&",
                    "schtasks",
                    "/Create",
                    "/TN",
                    WINDOWS_TASK_NAME_MINUTES_TRIGGER,
                    "/TR",
                    f"{args}",
                    "/SC",
                    "MINUTE",
                    "/MO",
                    str(interval_minutes),
                    "/F",
                ]
            )

    else:
        command = [
            "&",
            "schtasks",
            "/Delete",
            "/TN",
            WINDOWS_TASK_NAME_LOGON_TRIGGER,
            "/F",
            "&",
            "schtasks",
            "/Delete",
            "/TN",
            WINDOWS_TASK_NAME_MINUTES_TRIGGER,
            "/F",
        ]

        # remove leading '&'
        command = command[1:]

    if not __rerun_as_admin():
        log.debug(f"Running shell command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        # Check if it succeeded
        if result.returncode == 0:
            log.debug("Task config succeeded!")
        else:
            log.error("Task config failed!")
            log.error(
                f"Return Code: {result.returncode}",
            )

            if result.stderr:
                log.error(f'STDERR: "{result.stderr.strip()}"')


def __rerun_as_admin() -> bool:
    """Relaunch the current script with admin privileges if not already elevated"""
    import ctypes

    if ctypes.windll.shell32.IsUserAnAdmin():
        return False  # Already admin

    # Relaunch with elevated privileges
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        return True  # Exit current instance after launching elevated
    except Exception as e:
        print("Failed to elevate:", e)
        return False
