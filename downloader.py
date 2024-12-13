import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote
from mimetypes import guess_extension
import queue
import requests
import time
import threading
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import yt_dlp
import uuid
import mimetypes
import urllib.parse
import re
from urllib.parse import urlparse
from yt_dlp import YoutubeDL


def sanitize_filename(filename):
    """
    Sanitize filename by removing or replacing invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    # Remove or replace characters that are not allowed in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Truncate to a reasonable length
    sanitized = sanitized[:255]
    # Ensure the filename is not empty
    return sanitized.strip() or 'downloaded_audio'

def extract_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]

        return links
    except Exception as e:
        print(f"Failed to extract links: {e}")
        return []




def determine_url_type(url: str, prompt_user=None) -> str:
    """Determine the type of the given URL with optional user interaction."""
    try:
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            if prompt_user:
                return  prompt_user(url)
            return 'audio'

        response = requests.head(url, allow_redirects=True, timeout=10)
        content_type = response.headers.get('Content-Type', '').lower()
        print(content_type)

        if 'video' in content_type:
            if prompt_user:
              return prompt_user(url)
        elif 'audio' in content_type:
            return 'audio'
        elif 'image' in content_type:
            return 'image'
        elif 'text/html' in content_type:
            return 'html'
        else:
            return 'file'
    except requests.RequestException:
        return 'unknown'


def download_video(url, output_folder):
    try:
        text = 'best'
        ydl_opts = {
            'format': text,
            'outtmpl': f'{output_folder}/%(title)s_%(timestamp)s.%(ext)s',
            'overwrites': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Video downloaded successfully to {output_folder}")
    except Exception as e:
        print(f"Failed to download video: {e}")


import os
import subprocess
import yt_dlp
import requests


def download_audio(url, output_folder, use_fallback=True, timeout=30):
    """
    Download audio from a given URL with enhanced error handling and flexibility.

    Args:
        url (str): URL of the audio source
        output_folder (str): Directory to save the downloaded audio
        use_fallback (bool): Whether to use alternative download method if yt_dlp fails
        timeout (int): Timeout for download attempts in seconds

    Returns:
        str: Path to the downloaded audio file or None if download fails
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Check and set FFmpeg path if possible
    ffmpeg_paths = [
        '/usr/bin/ffmpeg',  # Linux standard path
        '/usr/local/bin/ffmpeg',  # Alternative Linux path
        'C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe',  # Windows common path
        'C:\\Program Files (x86)\\FFmpeg\\bin\\ffmpeg.exe'
    ]

    for path in ffmpeg_paths:
        if os.path.exists(path):
            os.environ['FFMPEG_PATH'] = path
            break

    try:
        # YouTube/streaming site download configuration
        if 'youtube.com' in url or 'youtu.be' in url:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': os.environ.get('FFMPEG_PATH', ''),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Convert to MP3 if not already
                mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
                return mp3_filename

        # Generic URL download fallback
        if use_fallback:
            try:
                # Direct download for non-YouTube URLs
                response = requests.get(url, stream=True, timeout=timeout)
                response.raise_for_status()

                # Determine filename
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    filename = os.path.basename(content_disposition.split('filename=')[-1].strip('"'))
                else:
                    # Generate filename from URL or use default
                    filename = os.path.basename(url).split('?')[0] or 'downloaded_audio.mp3'

                # Full path for saving
                filepath = os.path.join(output_folder, filename)

                # Save the file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return filepath

            except requests.RequestException as e:
                print(f"Fallback download failed: {e}")
                return None

    except Exception as e:
        print(f"Audio download error: {e}")
        return None







def download_image(url, output_folder, file_name=""):
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Disable SSL warnings if needed (use cautiously)
        requests.packages.urllib3.disable_warnings()

        # Download the image
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()

        # Verify content type is an image
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            raise ValueError("The URL does not point to an image.")

        # Determine file extension
        extension = content_type.split('/')[-1]

        # Generate unique filename
        if not file_name:
            # Use a combination of timestamp and unique identifier
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"downloaded_image_{timestamp}_{unique_id}.{extension}"
        elif '.' not in file_name:
            # Add extension if not provided
            file_name += f".{extension}"

        # Create full file path
        file_path = os.path.join(output_folder, file_name)

        # Ensure unique filename if file exists
        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1

        # Download and save the image
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

        print(f"Image downloaded successfully: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        print(f"Network error downloading image: {e}")
        return None
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None



def download_file(url, output_folder="downloads"):
    try:
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Make the HTTP request to get headers first
        response = requests.head(url, allow_redirects=True)
        response.raise_for_status()

        # Get the Content-Type
        content_type = response.headers.get("Content-Type", "")

        # Download the file with stream=True
        file_response = requests.get(url, stream=True)
        file_response.raise_for_status()

        file_name = url.split("/")[-1]

        if not file_name:
            file_name = "downloaded_file"

        # Determine the correct extension based on Content-Type
        file_extensions = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'text/plain': '.txt',
            'text/csv': '.csv',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif'
        }

        # Get extension from predefined dictionary or mimetypes
        if content_type in file_extensions:
            extension = file_extensions[content_type]
        else:
            extension = mimetypes.guess_extension(content_type.split(';')[0]) or ''

        # Add extension if not already present
        if not file_name.lower().endswith(extension.lower()) and extension:
            file_name += extension

        # Ensure unique filename
        base, ext = os.path.splitext(file_name)
        counter = 1
        file_path = os.path.join(output_folder, file_name)
        while os.path.exists(file_path):
            file_name = f"{base}_{counter}{ext}"
            file_path = os.path.join(output_folder, file_name)
            counter += 1

        # Write the content to the file
        with open(file_path, "wb") as file:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"File downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Network error downloading file: {e}")
        return None
    except Exception as e:
        print(f"Failed to download the file: {e}")
        return None
@dataclass
class DownloadTask:
    url: str
    filename: str
    priority: int = 0
    total_size: int = 0
    downloaded: int = 0
    status: str = "pending"
    error: Optional[str] = None
    speed: float = 0.0
    start_time: Optional[float] = None
    last_update_time: Optional[float] = None
    chunk_sizes: list[int] = None
    resumable: bool = False
    etag: Optional[str] = None

    def __post_init__(self):
        self.chunk_sizes = []

    def calculate_speed(self) -> float:
        """Calculate current download speed based on recent chunks"""
        if not self.chunk_sizes or not self.last_update_time:
            return 0.0


        recent_chunks = self.chunk_sizes[-5:]
        if not recent_chunks:
            return 0.0

        chunk_size = sum(recent_chunks)
        time_diff = time.time() - self.last_update_time
        if time_diff > 0:
            self.speed = chunk_size / time_diff

        return self.speed

    def estimate_time_remaining(self) -> Optional[int]:
        """Estimate seconds remaining based on current speed"""
        if self.speed <= 0 or self.total_size <= 0:
            return None

        remaining_bytes = self.total_size - self.downloaded
        return int(remaining_bytes / self.speed)


class PriorityDownloadQueue:
    """Priority queue for download tasks"""

    def __init__(self):
        self._queue = queue.PriorityQueue()
        self._tasks: Dict[str, DownloadTask] = {}
        self._lock = threading.Lock()

    def put(self, task: DownloadTask) -> None:
        with self._lock:
            self._tasks[task.url] = task
            self._queue.put((-task.priority, task.url))

    def get(self) -> Optional[DownloadTask]:
        try:
            _, url = self._queue.get_nowait()
            with self._lock:
                return self._tasks.get(url)
        except queue.Empty:
            return None

    def remove(self, url: str) -> None:
        with self._lock:
            if url in self._tasks:
                del self._tasks[url]

    def empty(self) -> bool:
        return self._queue.empty()


class RateLimiter:
    """Simple token bucket rate limiter"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
            self.last_update = now

            if tokens <= self.tokens:
                self.tokens -= tokens
                return True
            return False


class FileDownloader:
    def __init__(self,
                 download_folder: str,
                 min_workers: int = 2,
                 max_workers: int = 5,
                 rate_limit: Optional[float] = None):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.queue = PriorityDownloadQueue()
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.completed_downloads: Dict[str, DownloadTask] = {}

        if rate_limit:
            self.rate_limiter = RateLimiter(rate_limit, int(rate_limit * 2))
        else:
            self.rate_limiter = None

        self._setup_logging()
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="Downloader"
        )

    def _setup_logging(self):
        """Configure logging with both file and console handlers"""
        logger = logging.getLogger()
        logger.handlers.clear()

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))


        file_handler = logging.FileHandler(
            self.download_folder / 'downloader.log'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
        ))

        logger.addHandler(console)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)

    def download(self, task: DownloadTask, progress_callback: Optional[Callable] = None, prompt_user: Optional[Callable] = None):
        """Main method to download based on URL type with resume support and rate limiting."""
        task.status = "downloading"
        logging.info(f"Task {task.url} started downloading at {datetime.now()}")
        task.start_time = time.time()

        try:
            url = task.url
            logging.info(f"Attempting to download: {url}")
            url_type = determine_url_type(url,prompt_user=prompt_user)
            output_folder = str(self.download_folder)

            
            if progress_callback:
                progress_callback(task)

            if url_type == 'video':
                download_video(url, output_folder)
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"Video download completed: {url}")
                return

            if url_type == 'audio':
    
                download_audio(url, output_folder)
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"Audio download completed: {url}")
                return

            elif url_type == 'image':
                
                download_image(url, output_folder, task.filename)
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"Image download completed: {url}")
                return

            elif url_type == 'file':
                
                download_file(url, output_folder)
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"file download completed: {url}")
                return

            elif url_type == 'html':
                
                links = extract_links(url)
                logging.info(f"Extracted {len(links)} links from {url}")
                print(f"Extracted links: {links}")
                task.status = "completed"
                if progress_callback:
                    progress_callback(task)
                return

        
            try:
                
                headers = {}
                if task.resumable and task.downloaded > 0:
                    headers['Range'] = f'bytes={task.downloaded}-'
                if task.etag:
                    headers['If-Match'] = task.etag

                with requests.get(url, stream=True, headers=headers, timeout=30) as response:
                    response.raise_for_status()

                    if not task.filename:
                        task.filename = url.split('/')[-1] or "downloaded_file"

                    file_path = self.download_folder / task.filename

                    task.resumable = 'accept-ranges' in response.headers
                    task.etag = response.headers.get('etag')

                    if not task.total_size:
                        task.total_size = int(response.headers.get('content-length', 0))

                    mode = 'ab' if task.resumable and task.downloaded > 0 else 'wb'

                    with open(file_path, mode) as f:
                        current_downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk and (not self.rate_limiter or
                                        self.rate_limiter.acquire(len(chunk))):
                                f.write(chunk)
                                current_downloaded += len(chunk)
                                task.downloaded = current_downloaded
                                task.chunk_sizes.append(len(chunk))
                                task.last_update_time = time.time()

                                if progress_callback:
                                    task.calculate_speed()
                                    progress_callback(task)

                    task.status = "completed"
                    if progress_callback:
                        progress_callback(task)
                    logging.info(f"Download completed: {task.filename}")
                    self.completed_downloads[task.url] = task

            except requests.RequestException as e:
                download_file(url, output_folder)
                task.status = "completed"
                task.downloaded = task.total_size = 100
                if progress_callback:
                    progress_callback(task)
                logging.info(f"Generic file download completed: {url}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            if progress_callback:
                progress_callback(task)
            logging.error(f"Failed to download {task.url}: {e}")

            if "429" in str(e):  
                task.priority -= 1  
                self.queue.put(task)

        finally:
            if task.url in self.active_downloads:
                del self.active_downloads[task.url]
    # def _get_filename(self, url: str, response: requests.Response) -> str:
    #     """Extract and sanitize filename from response or URL"""
    #     filename = None

    #     # Try Content-Disposition header
    #     cd = response.headers.get('content-disposition')
    #     if cd and 'filename=' in cd:
    #         filename = cd.split('filename=')[1].strip('"\'')
    #         filename = unquote(filename)

    #     # Fall back to URL path
    #     if not filename:
    #         path = urlparse(url).path
    #         filename = os.path.basename(path)

    #     # If no extension, try to guess from content type
    #     if not os.path.splitext(filename)[1]:
    #         content_type = response.headers.get('content-type', '').split(';')[0]
    #         ext = guess_extension(content_type)
    #         if ext:
    #             filename = f"{filename}{ext}"

    #     # Ensure filename is unique
    #     base, ext = os.path.splitext(filename)
    #     counter = 1
    #     while (self.download_folder / filename).exists():
    #         filename = f"{base}_{counter}{ext}"
    #         counter += 1

    #     return filename

    def queue_download(self, url: str, filename: str = "", priority: int = 0) -> None:
        """Add a download task to the queue with optional priority"""
        task = DownloadTask(url=url, filename=filename, priority=priority)
        self.queue.put(task)
        self.active_downloads[url] = task
        logging.info(f"Queued download: {url} (priority: {priority})")

    def start_downloads(self, progress_callback: Optional[Callable] = None,prompt_user: Optional[Callable] = None) -> None:
        """Process download queue with dynamic thread adjustment"""
        try:
            active_futures = []

            while not self.queue.empty() or active_futures:
            
                optimal_workers = min(
                    self.max_workers,
                    max(self.min_workers, len(active_futures) + 1)
                )

                if len(active_futures) < optimal_workers:
                    task = self.queue.get()
                    if task:
                        future = self.executor.submit(
                            self.download,
                            task,
                            progress_callback,
                            prompt_user
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
            )
        }