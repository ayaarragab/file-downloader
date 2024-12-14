import logging
from abc import ABC, abstractmethod
from pathlib import Path


class BaseDownloader(ABC):
    def __init__(self, download_folder: str):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
    @abstractmethod
    def download(self, *args, **kwargs):
        """Abstract method for downloading files."""
        pass

    def _setup_logging(self):
        """Configure logging with both file and console handlers"""
        logger = logging.getLogger()
        logger.handlers.clear()

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        file_handler = logging.FileHandler(self.download_folder / "downloader.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
            )
        )

        logger.addHandler(console)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
