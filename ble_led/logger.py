import logging

LOGGER_NAME = "ble-led"

def setup_logger(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger
    
    level = logging.DEBUG if debug else logging.INFO

    logger.setLevel(level)

    handler = logging.StreamHandler()

    handler.setLevel(level)

    formatter = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger