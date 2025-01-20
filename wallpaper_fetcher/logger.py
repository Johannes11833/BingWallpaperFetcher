import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    format=FORMAT, datefmt="[%X]", handlers=[RichHandler(show_path=False)]
)


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
