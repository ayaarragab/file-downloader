import yt_dlp
from base_downloader import BaseDownloader

class VideoDownloader(BaseDownloader):
    def download(self, url: str, output_folder: str):
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{output_folder}/%(title)s_%(timestamp)s.%(ext)s',
                'overwrites': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"Video downloaded successfully to {output_folder}")
        except Exception as e:
            print(f"Failed to download video: {e}")
