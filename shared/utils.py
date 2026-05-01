# shared/utils.py
"""
Common utilities for the character recommender project.
"""
import re
import sys
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import logging

from shared.config import USER_AGENT, CRAWL_DELAY, MAX_RETRIES, TIMEOUT

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_page(url: str, delay: float = CRAWL_DELAY) -> Optional[str]:
    """
    Fetch a web page with retry logic and rate limiting.
    
    Args:
        url: URL to fetch
        delay: Seconds to wait before request (rate limiting)
    
    Returns:
        HTML content as string, or None if failed
    """
    time.sleep(delay)
    
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts")
    return None


def parse_html(html: str) -> BeautifulSoup:
    """Parse HTML content into BeautifulSoup object."""
    return BeautifulSoup(html, 'lxml')


def save_json(data: Any, filepath: Path) -> None:
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {filepath}")


def load_json(filepath: Path) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def slugify(text: str) -> str:
    """
    Convert text to a safe filename slug.
    
    Examples:
        "Brooklyn Nine-Nine" -> "brooklyn_nine_nine"
        "Are You Being Served?" -> "are_you_being_served"
        "It's Always Sunny" -> "its_always_sunny"
        "The Office (US)" -> "the_office_us"
    """
    if not text:
        return "unknown"
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace common characters
    slug = slug.replace("'", "")      # it's -> its
    slug = slug.replace("'", "")      # curly apostrophe
    slug = slug.replace("&", "and")   # & -> and
    
    # Remove characters not allowed in Windows filenames: < > : " / \ | ? *
    # Also remove other special characters
    slug = re.sub(r'[<>:"/\\|?*!,.\'\(\)\[\]{}]', '', slug)
    
    # Replace spaces and hyphens with underscores
    slug = re.sub(r'[\s\-]+', '_', slug)
    
    # Remove any non-alphanumeric characters (except underscores)
    slug = re.sub(r'[^a-z0-9_]', '', slug)
    
    # Remove multiple consecutive underscores
    slug = re.sub(r'_+', '_', slug)
    
    # Remove leading/trailing underscores
    slug = slug.strip('_')
    
    # Ensure it's not empty
    if not slug:
        return "unknown"
    
    # Limit length (Windows has path limits)
    if len(slug) > 100:
        slug = slug[:100].rstrip('_')
    
    return slug
    

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    import re
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove HTML artifacts
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def batch_list(items: list, batch_size: int):
    """Yield successive batches from a list."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]