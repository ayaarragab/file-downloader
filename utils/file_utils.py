import re

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
