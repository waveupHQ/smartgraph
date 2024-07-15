# smartgraph/logging.py

import logging
from typing import Optional


class SmartGraphLogger:
    _instance = None  # Singleton pattern to ensure only one instance of the logger exists.

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartGraphLogger, cls).__new__(cls)
            cls._instance._logger = logging.getLogger("SmartGraph")
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler("smartgraph.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._logger.critical(message, *args, **kwargs)

    @classmethod
    def get_logger(cls):
        return cls()

    def set_level(self, level: str):
        """Set the logging level.

        Args:
            level (str): The logging level. Can be 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        self._logger.setLevel(numeric_level)

    def add_file_handler(self, filename: str, level: Optional[str] = None):
        """Add a file handler to the logger.

        Args:
            filename (str): The name of the log file.
            level (str, optional): The logging level for this handler. Defaults to None (uses logger's level).
        """
        handler = logging.FileHandler(filename)
        if level:
            numeric_level = getattr(logging, level.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {level}")
            handler.setLevel(numeric_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)


# Usage example
if __name__ == "__main__":
    logger = SmartGraphLogger.get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Change log level
    logger.set_level("ERROR")

    # Add another file handler
    logger.add_file_handler("error.log", "ERROR")
