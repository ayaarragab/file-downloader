import os
import uuid
from datetime import datetime
import mimetypes
import requests
import threading
import logging
from .base_downloader import BaseDownloader


class ImageDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, file_name: str = "", cancellation_event=None):
        try:
            if cancellation_event is None:
                cancellation_event = threading.Event()
            os.makedirs(output_folder, exist_ok=True)
            if cancellation_event.is_set():
                logging.info("Image download stopped before starting")
                return None
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise ValueError("The URL does not point to an image.")

            extension = content_type.split("/")[-1] if "/" in content_type else None

            if not extension or len(extension) > 5:  # Prevent invalid extensions
                guessed_extension = mimetypes.guess_extension(response.headers.get("Content-Type", ""))
                extension = guessed_extension.lstrip(".") if guessed_extension else "jpg"  # Default to jpg

            if not file_name:
                unique_id = uuid.uuid4().hex[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"downloaded_image_{timestamp}_{unique_id}"
            if not file_name.endswith(f".{extension}"):
                file_name = f"{file_name}.{extension}"

            file_path = os.path.join(output_folder, file_name)

            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if cancellation_event.is_set():
                        file.close()
                        os.remove(file_path)
                        logging.info("Image download stopped")
                        return None
                    if chunk:
                        file.write(chunk)

            print(f"Image downloaded successfully: {file_path}")
            return file_path
        except requests.RequestException as e:
            if not cancellation_event.is_set():
                logging.info(f"Network error downloading image: {e}")
            return None
        except Exception as e:
            print(f"Failed to download image: {e}")
            return None
