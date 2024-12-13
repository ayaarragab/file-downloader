import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Optional


def extract_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True)]

        return links
    except Exception as e:
        print(f"Failed to extract links: {e}")
        return []


def determine_url_type(url: str, prompt_user=None) -> str:
    """Determine the type of the given URL with optional user interaction."""
    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.netloc or "facebook" or "youtu.be" in parsed_url.netloc:
            if prompt_user:
                return prompt_user(url)
            return "audio"

        response = requests.head(url, allow_redirects=True, timeout=10)
        content_type = response.headers.get("Content-Type", "").lower()
        print(content_type)

        if "video" in content_type:
            if prompt_user:
                return prompt_user(url)
        elif "audio" in content_type:
            return "audio"
        elif "image" in content_type:
            return "image"
        elif "text/html" in content_type:
            return "html"
        else:
            return "file"
    except requests.RequestException:
        return "unknown"
