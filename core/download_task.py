import time
from dataclasses import dataclass
from typing import Optional


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
    choice: str = None
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
