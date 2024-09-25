import logging
import sys

LOGGER = logging.getLogger(__name__)

if not LOGGER.hasHandlers():
    FORMATTER = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    CONSOLE = logging.StreamHandler(stream=sys.stdout)
    CONSOLE.setFormatter(FORMATTER)
    LOGGER.addHandler(CONSOLE)