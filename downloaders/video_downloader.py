import threading
import yt_dlp
from .base_downloader import BaseDownloader
import logging

class VideoDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, cancellation_event: threading.Event = None):
        try:
            if cancellation_event is None:
                cancellation_event = threading.Event()
            
            def progress_hook(a):
                if cancellation_event.is_set():
                    logging.info("Download stopped by user")

            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{output_folder}/%(title)s_%(timestamp)s.%(ext)s',
                'overwrites': True,
                'progress_hooks': [progress_hook],
                'no_warnings': True,
                'quiet': False
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if cancellation_event.is_set():
                    logging.info("Download cancelled before starting")
                    return
                
                ydl.download([url])
            
            logging.info(f"Video downloaded successfully to {output_folder}")
        except yt_dlp.utils.DownloadCancelled:
            logging.info("Download was cancelled")
            return None
        except yt_dlp.utils.DownloadError as e:
            if not cancellation_event.is_set():
                logging.info(f"Failed to download video: {e}")
        except Exception as e:
            if not cancellation_event.is_set():
                logging.info(f"Unexpected error during download: {e}")
