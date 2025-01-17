import platform
import shutil
import subprocess

from bingwallpaper import APP_NAME, VERSION


def install():

    name = APP_NAME.replace(" ", "-").lower()
    subprocess.run(
        args=[
            "pyinstaller",
            "./bingwallpaper/wallpaper_fetcher.py",
            f"--name={name}",
            "--noconfirm",
            "--icon=res/app.png",
        ]
    )

    # zip the pyinstaller output as an artifact
    os_name = platform.system().replace("Darwin", "Mac").lower()
    output_path = f"dist/{name}-{VERSION}-{os_name}"
    print("Creating archive")
    shutil.make_archive(output_path, "zip", f"dist/{name}")


if __name__ == "__main__":
    install()
