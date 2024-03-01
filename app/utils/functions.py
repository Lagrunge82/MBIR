import logging


def configure_logger(name: str, level: int = None, file: str = None):
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    if file:
        file_handler = logging.FileHandler(file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - @%(module)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
