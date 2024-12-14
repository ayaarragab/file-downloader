import mimetypes
import os
import logging
import requests
import threading
from .base_downloader import BaseDownloader


class FileDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, cancellation_event=None):
        try:
            if cancellation_event is None:
                cancellation_event = threading.Event()
            os.makedirs(output_folder, exist_ok=True)
            if cancellation_event.is_set():
                logging.info("File download stopped before starting")
                return None
            response = requests.get(url, stream=True)
            response.raise_for_status()

            file_name = url.split("/")[-1] or "downloaded_file"
            content_type = response.headers.get("Content-Type", "")
            extension = mimetypes.guess_extension(content_type.split(";")[0]) or ""

            if not file_name.endswith(extension):
                file_name += extension

            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if cancellation_event.is_set():
                        file.close()
                        os.remove(file_path)
                        logging.info("File download stopped")
                        return None
                    if chunk:
                        file.write(chunk)
            print(f"File downloaded successfully: {file_path}")
        except requests.RequestException as e:
            if not cancellation_event.is_set():
                logging.info(f"Network error downloading file: {e}")
            return None
        except Exception as e:
            print(f"Failed to download file: {e}")
