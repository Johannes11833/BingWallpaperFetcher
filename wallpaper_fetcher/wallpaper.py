from pathlib import Path
from typing import Dict


class WallPaper:
    def __init__(
        self,
        title: str,
        url: str,
        startdate: int,
        enddate: int,
        copyright: str,
        raw: dict,
        path: Path | None,
    ):
        self.title = title
        self.url = url
        self.startdate = startdate
        self.enddate = enddate
        self.copyright = copyright
        self.raw = raw
        self.path = path

    @classmethod
    def from_json(cls, content: Dict, path: Path | None = None):
        return cls(
            title=content["title"],
            # content["url"] holds the rest of the url
            url="https://bing.com" + content["url"],
            startdate=content["startdate"],
            enddate=content["enddate"],
            copyright=content["copyright"],
            raw=content,
            path=path,
        )

    def pretty_print(self) -> str:
        return f'Wallpaper(title: "{self.title}", copyright: "{self.copyright}", startdate: {self.startdate}, path: "{self.path}")'

    def __repr__(self):
        return self.pretty_print()
