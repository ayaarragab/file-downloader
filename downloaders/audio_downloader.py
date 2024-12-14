import threading
import yt_dlp
import os
import logging
import requests
import time
from .base_downloader import BaseDownloader

class AudioDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, cancellation_event: threading.Event = None):
        # Create a flag to track download progress
        download_started = threading.Event()
        download_completed = threading.Event()
        
        # Ensure we have a cancellation event
        if cancellation_event is None:
            cancellation_event = threading.Event()

        # Create a more aggressive cancellation thread
        def cancellation_monitor():
            while not download_completed.is_set():
                if cancellation_event.is_set():
                    logging.info(f"Cancellation requested for {url}")
                    
                    # If download has started but not completed, interrupt
                    if download_started.is_set() and not download_completed.is_set():
                        # Attempt to interrupt the download more aggressively
                        yt_dlp.utils.std_headers['User-Agent'] = 'Cancel-Download-Request'
                        break
                
                time.sleep(0.1)  # Prevent busy waiting
        
        # Monitoring thread for cancellation
        monitor_thread = threading.Thread(target=cancellation_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            os.makedirs(output_folder, exist_ok=True)
            
            if cancellation_event.is_set():
                logging.info("Audio File download stopped before starting")
                return None

            # Paths to check for ffmpeg
            ffmpeg_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe",
                "C:\\Program Files (x86)\\FFmpeg\\bin\\ffmpeg.exe",
            ]

            for path in ffmpeg_paths:
                if os.path.exists(path):
                    os.environ["FFMPEG_PATH"] = path
                    break

            # YouTube download specific handling
            if "youtube.com" in url or "youtu.be" in url:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(output_folder, "%(title)s.%(ext)s"),
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                    "ffmpeg_location": os.environ.get("FFMPEG_PATH", ""),
                    'no_warnings': True,
                    'quiet': True,
                    'no_color': True,
                    'no_progress': True
                }

                # Progress hook to track download and check cancellation
                def progress_hook(d):
                    # Mark that download has started
                    download_started.set()
                    
                    # Check if cancellation was requested
                    if cancellation_event.is_set():
                        logging.info("Cancellation detected in progress hook")
                        raise yt_dlp.utils.DownloadCancelled("Download manually stopped")
                
                ydl_opts['progress_hooks'] = [progress_hook]

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        if cancellation_event.is_set():
                            logging.info("Audio download cancelled before yt-dlp started.")
                            return None
                        
                        # Actual download attempt
                        try:
                            info = ydl.download([url])
                            
                            # Mark download as completed
                            download_completed.set()
                            
                            # If download completes, prepare filename
                            if info and len(info) > 0:
                                filename = ydl.prepare_filename(info[0])
                                mp3_filename = filename.rsplit(".", 1)[0] + ".mp3"
                                
                                # Final check before returning filename
                                if cancellation_event.is_set():
                                    # Remove the file if it was created
                                    if os.path.exists(mp3_filename):
                                        os.remove(mp3_filename)
                                    return None
                                
                                return mp3_filename
                        
                        except yt_dlp.utils.DownloadCancelled:
                            logging.info("Download was manually cancelled")
                            return None

                except Exception as e:
                    logging.error(f"YouTube download error: {e}")
                    return None

            # Fallback download method for non-YouTube sources
            return None

        except Exception as e:
            logging.error(f"Unexpected error in AudioDownloader: {e}")
            return None
        finally:
            # Ensure download_completed is set to allow monitor thread to exit
            download_completed.set()
