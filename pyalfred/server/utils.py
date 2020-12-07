import logging


def make_base_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.setLevel(logging.DEBUG)

    return logger