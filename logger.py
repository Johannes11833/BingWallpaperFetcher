import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])


log = logging.getLogger(__name__)
