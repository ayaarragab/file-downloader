import os
import requests
import yt_dlp
from .base_downloader import BaseDownloader

class AudioDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str, use_fallback=True, timeout=30):
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
