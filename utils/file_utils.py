import re

def sanitize_filename(filename):
    """
    Sanitize filename by removing or replacing invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = sanitized[:255]
    return sanitized.strip() or 'downloaded_audio' 
