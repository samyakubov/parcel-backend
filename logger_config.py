import os
import logging

def setup_logger(logger_name: str, log_file: str, level: int = logging.DEBUG) -> logging.Logger:
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(log_dir, log_file))
    c_handler.setLevel(logging.WARNING)
    f_handler.setLevel(level)

    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger

logger = setup_logger("System_Logger", "sys.log")

