import logging

from core.config import LogLevel


def level_to_int(level: LogLevel) -> int:
    return logging.getLevelNamesMapping()[level.upper()]


def configure_logging(level: LogLevel) -> None:
    logging.basicConfig(
        level=level_to_int(level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
