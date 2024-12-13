import os
import requests
import uuid
from datetime import datetime
from .base_downloader import BaseDownloader

class ImageDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, file_name: str = ""):
        try:
            os.makedirs(output_folder, exist_ok=True)
            response = requests.get(url, stream=True, verify=False)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                raise ValueError("The URL does not point to an image.")

            extension = content_type.split('/')[-1]
            if not file_name:
                unique_id = uuid.uuid4().hex[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"downloaded_image_{timestamp}_{unique_id}.{extension}"

            file_path = os.path.join(output_folder, file_name)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            print(f"Image downloaded successfully: {file_path}")
        except Exception as e:
            print(f"Failed to download image: {e}")
