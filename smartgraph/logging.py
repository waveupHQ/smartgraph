import logging
from typing import Optional


class SmartGraphLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartGraphLogger, cls).__new__(cls)
            cls._instance._logger = logging.getLogger("SmartGraph")
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        self._logger.setLevel(logging.DEBUG)  # Set to DEBUG by default
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)

    def critical(self, message: str):
        self._logger.critical(message)

    @classmethod
    def get_logger(cls):
        return cls()

    def set_level(self, level: str):
        """Set the logging level."""
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        self._logger.setLevel(numeric_level)

    def add_file_handler(self, filename: str, level: Optional[str] = None):
        """Add a file handler to the logger."""
        handler = logging.FileHandler(filename)
        if level:
            numeric_level = getattr(logging, level.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {level}")
            handler.setLevel(numeric_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
