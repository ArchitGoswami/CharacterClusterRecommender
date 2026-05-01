# scripts/crawler_tvtropes.py
"""
TVTropes crawler for character tropes and descriptions.

Phase: 1 (Days 1-2)

TVTropes Structure:
- Character pages: https://tvtropes.org/pmwiki/pmwiki.php/Characters/{ShowName}
- Contains: Character names, associated tropes, descriptions

Output: data/raw/tvtropes/{media_slug}.json
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from tqdm import tqdm

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.utils import fetch_page, parse_html, save_json, load_json, slugify, logger
from shared.config import RAW_DIR, TITLES_MASTER_FILE


TVTROPES_BASE = "https://tvtropes.org"
TVTROPES_CHARACTERS = f"{TVTROPES_BASE}/pmwiki/pmwiki.php/Characters"


def get_character_page_url(media_title: str) -> str:
    """Generate TVTropes character page URL for a media title."""
    # TVTropes uses CamelCase without spaces
    camel_case = ''.join(word.capitalize() for word in media_title.split())
    # Remove special characters
    camel_case = re.sub(r'[^a-zA-Z0-9]', '', camel_case)
    return f"{TVTROPES_CHARACTERS}/{camel_case}"


def parse_character_page(html: str, media_title: str) -> List[Dict]:
    """
    Parse a TVTropes character page to extract characters and tropes.
    
    Args:
        html: Raw HTML of character page
        media_title: Name of the show/movie
    
    Returns:
        List of character dictionaries with tropes
    """
    soup = parse_html(html)
    characters = []
    
    # TVTropes character pages typically have folders for different characters
    # Each folder contains tropes listed for that character
    
    # Find all character folders/sections
    folders = soup.find_all('div', class_='folderlabel')
    
    for folder in folders:
        char_name = folder.get_text(strip=True)
        
        # Skip non-character sections
        if any(skip in char_name.lower() for skip in ['tropes', 'general', 'spoiler', 'main']):
            continue
        
        # Find the content after this folder
        folder_content = folder.find_next_sibling('div', class_='folder')
        if not folder_content:
            continue
        
        # Extract tropes (usually in list items with links)
        tropes = []
        trope_links = folder_content.find_all('a', class_='twikilink')
        for link in trope_links:
            href = link.get('href', '')
            if '/Main/' in href:
                trope_name = href.split('/Main/')[-1]
                tropes.append(trope_name)
        
        # Extract description text
        description_parts = []
        for p in folder_content.find_all(['p', 'li']):
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                description_parts.append(text)
        
        description = ' '.join(description_parts[:5])  # First 5 paragraphs
        
        if char_name and (tropes or description):
            characters.append({
                "name": char_name,
                "media_title": media_title,
                "tropes": list(set(tropes)),  # Deduplicate
                "description": description[:2000],  # Limit length
                "source": "tvtropes"
            })
    
    return characters


def crawl_tvtropes_for_title(media_title: str) -> Optional[Dict]:
    """
    Crawl TVTropes for a single media title.
    
    Args:
        media_title: Name of show/movie
    
    Returns:
        Dictionary with characters and metadata, or None if failed
    """
    url = get_character_page_url(media_title)
    logger.info(f"Crawling TVTropes: {url}")
    
    html = fetch_page(url)
    if not html:
        return None
    
    characters = parse_character_page(html, media_title)
    
    if not characters:
        logger.warning(f"No characters found for {media_title}")
        return None
    
    return {
        "media_title": media_title,
        "url": url,
        "characters": characters,
        "character_count": len(characters)
    }


def crawl_all_titles(titles: List[str], output_dir: Path = RAW_DIR / "tvtropes") -> Dict:
    """
    Crawl TVTropes for all titles in the list.
    
    Args:
        titles: List of media titles to crawl
        output_dir: Directory to save raw data
    
    Returns:
        Summary statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {"total": len(titles), "success": 0, "failed": 0, "characters": 0}
    
    for title in tqdm(titles, desc="Crawling TVTropes"):
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Skip if already crawled
        if output_file.exists():
            logger.info(f"Skipping {title} (already crawled)")
            data = load_json(output_file)
            stats["success"] += 1
            stats["characters"] += data.get("character_count", 0)
            continue
        
        result = crawl_tvtropes_for_title(title)
        
        if result:
            save_json(result, output_file)
            stats["success"] += 1
            stats["characters"] += result["character_count"]
        else:
            stats["failed"] += 1
    
    logger.info(f"TVTropes crawl complete: {stats}")
    return stats


def main():
    """Main entry point for TVTropes crawler."""
    # Load master title list
    if TITLES_MASTER_FILE.exists():
        titles_data = load_json(TITLES_MASTER_FILE)
        titles = [t["title"] for t in titles_data]
    else:
        # Fallback: test with a few titles
        titles = [
            "Brooklyn Nine-Nine",
            "The Office",
            "Parks and Recreation",
            "New Girl",
            "Arrested Development",
            "Seinfeld",
            "Friends",
            "How I Met Your Mother",
            "The Good Place",
            "Schitts Creek"
        ]
        logger.warning(f"No master title list found, using {len(titles)} test titles")
    
    stats = crawl_all_titles(titles)
    print(f"\nCrawl Summary: {stats}")


if __name__ == "__main__":
    main()