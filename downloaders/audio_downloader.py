import os
import logging
import requests
import yt_dlp
import threading

from .base_downloader import BaseDownloader


class AudioDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, use_fallback=True, timeout=30, cancellation_event=None):
        if cancellation_event is None:
                cancellation_event = threading.Event()
        os.makedirs(output_folder, exist_ok=True)
        if cancellation_event.is_set():
                logging.info("Audio File download stopped before starting")
                return None
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

        try:
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
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_filename = filename.rsplit(".", 1)[0] + ".mp3"
                    return mp3_filename

            if use_fallback:
                try:
                    response = requests.get(url, stream=True, timeout=timeout)
                    response.raise_for_status()

                    content_disposition = response.headers.get("content-disposition")
                    if content_disposition:
                        filename = os.path.basename(
                            content_disposition.split("filename=")[-1].strip('"')
                        )
                    else:
                        filename = (
                            os.path.basename(url).split("?")[0]
                            or "downloaded_audio.mp3"
                        )

                    filepath = os.path.join(output_folder, filename)

                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if cancellation_event.is_set():
                                f.close()
                                os.remove(filepath)
                                logging.info("Audio File download stopped")
                                return None
                            f.write(chunk)

                    return filepath

                except requests.RequestException as e:
                    print(f"Fallback download failed: {e}")
                    return None

        except Exception as e:
            print(f"Audio download error: {e}")
            return None
