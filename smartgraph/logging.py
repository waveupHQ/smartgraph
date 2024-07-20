# smartgraph/logging.py

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


class SmartGraphLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartGraphLogger, cls).__new__(cls)
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        # Define a custom theme for our logger
        custom_theme = Theme(
            {
                "info": "cyan",
                "warning": "yellow",
                "error": "bold red",
                "critical": "bold white on red",
            }
        )

        # Create a Rich console with our custom theme
        console = Console(theme=custom_theme)

        # Configure the RichHandler
        rich_handler = RichHandler(
            console=console, show_time=True, show_path=True, markup=True, rich_tracebacks=True
        )

        # Create and configure the logger
        self._logger = logging.getLogger("SmartGraph")
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(rich_handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        self._logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False):
        self._logger.critical(message, exc_info=exc_info)

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
        file_handler = logging.FileHandler(filename)
        if level:
            numeric_level = getattr(logging, level.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {level}")
            file_handler.setLevel(numeric_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
