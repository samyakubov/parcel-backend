import logging
import os


def setup_logger(logger_name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Sets up a logger with console and file handlers.

    Args:
        logger_name (str): The name of the logger.
        level (int, optional): The logging level. Defaults to logging.DEBUG.

    Returns:
        logging.Logger: The configured logger.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Create a logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Console Handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(level)
    c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)

    # File Handler
    f_handler = logging.FileHandler("logs/app.log")
    f_handler.setLevel(logging.WARNING)  # Log warnings and above to a file
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    f_handler.setFormatter(f_format)

    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger


logger = setup_logger("System_Logger")
