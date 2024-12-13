import os
import mimetypes
import requests
from .base_downloader import BaseDownloader

class FileDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str):
        try:
            os.makedirs(output_folder, exist_ok=True)
            response = requests.get(url, stream=True)
            response.raise_for_status()

            file_name = url.split("/")[-1] or "downloaded_file"
            content_type = response.headers.get("Content-Type", "")
            extension = mimetypes.guess_extension(content_type.split(';')[0]) or ''

            if not file_name.endswith(extension):
                file_name += extension

            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            print(f"File downloaded successfully: {file_path}")
        except Exception as e:
            print(f"Failed to download file: {e}")
