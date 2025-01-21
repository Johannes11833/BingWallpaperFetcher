import platform
import shutil
import subprocess

from wallpaper_fetcher import APP_NAME, VERSION


def install():

    name = APP_NAME.replace(" ", "-").lower()
    process = subprocess.run(
        args=[
            "pyinstaller",
            "./wallpaper_fetcher/fetcher.py",
            f"--name={name}",
            "--noconfirm",
            "--icon=res/app.png",
        ]
    )

    if process.returncode == 0:
        # zip the pyinstaller output as an artifact
        os_name = platform.system().replace("Darwin", "Mac").lower()
        output_path = f"dist/{name}-{VERSION}-{os_name}"
        print("Creating archive")
        shutil.make_archive(output_path, "zip", f"dist/{name}")


if __name__ == "__main__":
    install()
