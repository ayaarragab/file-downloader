import queue
import threading
from typing import Dict, Optional

from .download_task import DownloadTask


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
