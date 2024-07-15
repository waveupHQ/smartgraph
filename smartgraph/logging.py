from __future__ import annotations

import logging
from typing import Any, Optional

# Constants
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO


class SmartGraphLogger:
    _instance: Optional[SmartGraphLogger] = None

    def __new__(cls) -> SmartGraphLogger:
        if cls._instance is None:
            cls._instance = super(SmartGraphLogger, cls).__new__(cls)
            cls._instance._logger = logging.getLogger("SmartGraph")
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self) -> None:
        self._logger.setLevel(DEFAULT_LOG_LEVEL)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(DEFAULT_LOG_LEVEL)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler("smartgraph.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(message, *args, **kwargs)

    @classmethod
    def get_logger(cls) -> SmartGraphLogger:
        return cls()

    def set_level(self, level: str) -> None:
        """Set the logging level.

        Args:
            level (str): The logging level. Can be 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        self._logger.setLevel(numeric_level)

    def add_file_handler(self, filename: str, level: Optional[str] = None) -> None:
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
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
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
