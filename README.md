# file-downloader

## Overview

This Advanced Download Manager is a robust, flexible Python library for downloading various types of content from the internet with advanced features like priority queuing, rate limiting, and comprehensive progress tracking.

## Features

- 🌐 Multi-type Download Support
  - Videos
  - Audio files
  - Images
  - Generic files
  - Web page link extraction

- 🚀 Advanced Download Management
  - Priority-based download queue
  - Bandwidth rate limiting
  - Resumable downloads
  - Detailed progress tracking

- 🔒 Robust Error Handling
  - Comprehensive error logging
  - Automatic retry mechanisms
  - Detailed download status reporting

- 🧵 Concurrent Download Support
  - Dynamic thread pool management
  - Configurable worker threads
  - Thread-safe implementations

## Installation

### Prerequisites

- Python 3.8+
- pip

### Dependencies

```bash
pip install -r requirements.txt
```

Required libraries:
- requests
- yt-dlp
- beautifulsoup4

## Quick Start

### Basic Usage

```python
from download_manager.managers.download_manager import FileDownloader

# Initialize downloader
downloader = FileDownloader(download_folder='downloads')

# Add download tasks
downloader.queue_download('https://example.com/video.mp4', priority=1)
downloader.queue_download('https://example.com/audio.mp3', priority=2)

# Start downloads
downloader.start_downloads()
```

### Advanced Usage with Progress Callback

```python
def progress_callback(task):
    print(f"Download Progress: {task.filename}")
    print(f"  Status: {task.status}")
    print(f"  Progress: {task.downloaded}/{task.total_size} bytes")
    print(f"  Speed: {task.speed} bytes/sec")

downloader.start_downloads(progress_callback=progress_callback)
```

## Configuration

### FileDownloader Parameters

- `download_folder`: Destination for downloaded files
- `min_workers`: Minimum concurrent download threads
- `max_workers`: Maximum concurrent download threads
- `rate_limit`: Optional bandwidth limitation

## Modules

- `core/`: Core data structures and algorithms
- `utils/`: Utility functions for URL handling
- `downloaders/`: Specific download implementations
- `managers/`: Download management logic
- `exceptions/`: Custom exception handling

## Logging

Logs are generated in the download folder with:
- Console logging
- File-based detailed logging
- Configurable log levels

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Troubleshooting

- Ensure all dependencies are installed
- Check network connectivity
- Verify URL accessibility
- Review log files for detailed error information

## Performance Considerations

- Adjust `min_workers` and `max_workers` based on your system
- Use rate limiting for controlled bandwidth usage
- Monitor system resources during large downloads

## Future Roadmap

- [ ] Add support for more download protocols
- [ ] Implement more sophisticated retry mechanisms
- [ ] Create a CLI interface
- [ ] Add proxy support
- [ ] Enhance error recovery strategies

## Contact

For issues, feature requests, or contributions, please open a GitHub issue.
