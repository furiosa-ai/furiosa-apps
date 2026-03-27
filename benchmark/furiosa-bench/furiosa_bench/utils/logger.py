import logging
import sys

logger = logging.getLogger("furiosa_bench")


def setup_logger(loglevel: str) -> None:
    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(loglevel.upper())
    logger.propagate = False
