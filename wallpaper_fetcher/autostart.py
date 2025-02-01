from enum import Enum
from pathlib import Path
import platform
import sys
from typing import Any, Iterable, List
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
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_ITEM_NAME = APP_NAME.replace(" ", "")

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
        launch_args.insert(0, sys.executable)

    return launch_args


def autostart_supported() -> bool:
    return OS in [OperatingSystem.WINDOWS, OperatingSystem.LINUX]


def set_auto_start(enable: bool, args: Iterable[str] = ()) -> bool:
    launch_args = " ".join(f'"{a}"' for a in args)
    result = False
    if OS == OperatingSystem.WINDOWS:
        if enable:
            result = __set_reg_item(REG_PATH, REG_ITEM_NAME, f"{launch_args}")
            log.debug(f"set_reg_item {REG_PATH}/{REG_ITEM_NAME}: {result}")
        else:
            result = __delete_reg_item(REG_PATH, REG_ITEM_NAME)
            log.debug(f"delete_reg_item {REG_PATH}/{REG_ITEM_NAME}: {result}")
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
        result: str = __get_reg_item(REG_PATH, REG_ITEM_NAME)
        return (
            # a value is set
            result != None
            # the executable exists (it might have been moved by the user)
            and Path(result[1:].split('"')[0].replace('"', "")).is_file()
        )
    elif OS == OperatingSystem.LINUX:
        return LINUX_LAUNCH_FILE_PATH.is_file()
    else:
        log.warning(f"{OS} is not supported (get_autostart_enabled)")
        return False


# ---------------------------------- WINDOWS --------------------------------- #
if OS == OperatingSystem.WINDOWS:
    import winreg


def __set_reg_item(path: str, name: str, value: str) -> bool:
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as registry_key:
            winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
            return True
    except WindowsError:
        return False


def __get_reg_item(path: str, name: str) -> Any:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ
        ) as registry_key:
            value, _ = winreg.QueryValueEx(registry_key, name)
            return value
    except WindowsError:
        return None


def __delete_reg_item(path, name) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS
        ) as registry_key:
            winreg.DeleteValue(registry_key, name)
            return True
    except WindowsError as e:
        log.debug(e)
        return False
