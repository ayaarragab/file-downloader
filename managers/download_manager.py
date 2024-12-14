import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.download_task import DownloadTask
from core.priority_queue import PriorityDownloadQueue
from core.rate_limiter import RateLimiter
from downloaders.audio_downloader import AudioDownloader
from downloaders.file_downloader import FileDownloader
from downloaders.image_downloader import ImageDownloader
from downloaders.video_downloader import VideoDownloader
from utils.url_utils import determine_url_type


class DownloadManager:
    def __init__(
        self,
        download_folder: str,
        min_workers: int = 2,
        max_workers: int = 5,
        rate_limit: Optional[float] = None,
    ):
        """
        Initialize the Download Manager.

        Args:
            download_folder (str): Path to the download folder.
            min_workers (int): Minimum number of worker threads.
            max_workers (int): Maximum number of worker threads.
            rate_limit (float, optional): Rate limit for downloads in bytes per second.
        """
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="Downloader"
        )

        self.queue = PriorityDownloadQueue()

        self.active_downloads: Dict[str, Any] = {}
        self.completed_downloads: Dict[str, Any] = {}

        self.rate_limiter = (
            RateLimiter(rate_limit, int(rate_limit * 2)) if rate_limit else None
        )

        self.video_downloader = VideoDownloader(download_folder)
        self.audio_downloader = AudioDownloader(download_folder)
        self.image_downloader = ImageDownloader(download_folder)
        self.file_downloader = FileDownloader(download_folder)
        self.cancellation_events: Dict[str, threading.Event] = {}


    def download(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable] = None,
        prompt_user: Optional[Callable] = None,
    ):
        """Main method to download based on URL type."""
        cancellation_event = threading.Event()
        self.cancellation_events[task.url] = cancellation_event
        logging.info("It is adedddeded")
        task.status = "downloading"
        logging.info(f"Task {task.url} started downloading at {datetime.now()}")
        task.start_time = time.time()

        try:
            url = task.url
            logging.info(f"Attempting to download: {url}")
            url_type = None
            if task.choice:
                url_type = task.choice
            else:
                determine_url_type(url, prompt_user=prompt_user)
            output_folder = str(self.download_folder)

            if progress_callback:
                progress_callback(task)
            if url_type == "video":
                self.video_downloader.download(url, output_folder, cancellation_event)
            elif url_type == "audio":
                self.audio_downloader.download(url, output_folder, cancellation_event)
            elif url_type == "image":
                self.image_downloader.download(url, output_folder, task.filename, cancellation_event)
            elif url_type == "pdf":
                self.file_downloader.download(url, output_folder, cancellation_event)
            else:
                logging.error(f"Unknown URL type: {url_type}")
                task.status = "failed"
                return
            
            if cancellation_event.is_set():
                task.status = "stopped"
                logging.info(f"Download cancelled: {url}")
            else:
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"Download completed: {url}")

        except Exception as e:
            if not cancellation_event.is_set():
                task.status = "failed"
                task.error = str(e)
                if progress_callback:
                    progress_callback(task)
                logging.error(f"Failed to download {task.url}: {e}")

        finally:
            if task.url in self.active_downloads:
                del self.active_downloads[task.url]
            
            if task.url in self.cancellation_events:
                del self.cancellation_events[task.url]

    def queue_download(self, url: str, filename: str = "", priority: int = 0, choice=None) -> None:
        """Add a download task to the queue with optional priority"""
        task = DownloadTask(url=url, filename=filename, priority=priority, choice=choice)
        self.queue.put(task)
        self.active_downloads[url] = task
        logging.info(f"Queued download: {url} (priority: {priority})")

    def start_downloads(
        self,
        progress_callback: Optional[Callable] = None,
        prompt_user: Optional[Callable] = None,
    ) -> None:
        """Process download queue with dynamic thread adjustment"""
        try:
            active_futures = []

            while not self.queue.empty() or active_futures:

                optimal_workers = min(
                    self.max_workers, max(self.min_workers, len(active_futures) + 1)
                )

                if len(active_futures) < optimal_workers:
                    task = self.queue.get()
                    if task:
                        future = self.executor.submit(
                            self.download, task, progress_callback, prompt_user
                        )
                        active_futures.append(future)

                done, active_futures = self.wait_for_futures(active_futures)

        except Exception as e:
            logging.error(f"Error in download manager: {e}")
            raise

    def wait_for_futures(self, futures: list) -> tuple[list, list]:
        """Wait for some futures to complete and handle results"""
        done = []
        still_active = []

        for future in futures:
            if future.done():
                try:
                    future.result()
                    done.append(future)
                except Exception as e:
                    logging.error(f"Future failed: {e}")
                    done.append(future)
            else:
                still_active.append(future)

        return done, still_active

    def pause_download(self, url: str) -> None:
        """Pause a download by removing it from active downloads"""
        if url in self.active_downloads:
            task = self.active_downloads[url]
            task.status = "paused"
            self.queue.remove(url)

    def resume_download(self, url: str) -> None:
        """Resume a paused download"""
        if url in self.active_downloads:
            task = self.active_downloads[url]
            if task.status == "paused":
                task.status = "pending"
                self.queue.put(task)

    def get_download_stats(self) -> Dict[str, Any]:
        """Get current download statistics"""
        active_count = len(self.active_downloads)
        completed_count = len(self.completed_downloads)
        total_downloaded = sum(
            task.downloaded for task in self.active_downloads.values()
        )

        return {
            "active_downloads": active_count,
            "completed_downloads": completed_count,
            "total_downloaded": total_downloaded,
            "download_speed": sum(
                task.speed for task in self.active_downloads.values()
            ),
        }

    def stop_download(self, url: str) -> None:
        matching_task = next((task for task in self.active_downloads.values() if task.url == url), None)
        
        if matching_task:
            url_to_stop = matching_task.url
            
            if url_to_stop in self.cancellation_events:
                self.cancellation_events[url_to_stop].set()
            
            matching_task.status = "stopped"
            self.active_downloads.pop(url_to_stop, None)
            logging.info(f"Download for {url_to_stop} has been stopped.")
        else:
            matching_task = next((task for task in self.active_downloads.values() 
                                if url in task.url or task.url in url), None)
            
            if matching_task:
                url_to_stop = matching_task.url
                
                if url_to_stop in self.cancellation_events:
                    self.cancellation_events[url_to_stop].set()
                
                matching_task.status = "stopped"
                self.active_downloads.pop(url_to_stop, None)
                logging.info(f"Download for {url_to_stop} has been stopped.")
            else:
                logging.error(f"No active download found for {url}")
