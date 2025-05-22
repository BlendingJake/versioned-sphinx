from os import environ
from sys import stdout
import logging


ROOT_LOGGER = logging.getLogger("versioned-sphinx")
ROOT_LOGGER.setLevel(environ.get("LOG", "INFO").upper())
_handler = logging.StreamHandler(stream=stdout)
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
)
ROOT_LOGGER.addHandler(_handler)


def get_logger(name: str) -> logging.Logger:
    return ROOT_LOGGER.getChild(name)
