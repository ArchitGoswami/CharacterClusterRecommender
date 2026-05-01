# scripts/crawler_fandom.py
"""
Fandom wiki crawler for character information.

Owner: Archit
Phase: 1 (Days 1-2)

Output: data/raw/fandom/{media_slug}.json
"""

import re
import sys
import time
import cloudscraper
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from shared.utils import parse_html, save_json, load_json, slugify, logger
from shared.config import RAW_DIR, TITLES_MASTER_FILE


# ============== FANDOM-SPECIFIC SCRAPER ==============
# Use cloudscraper to bypass Cloudflare protection

FANDOM_SCRAPER = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)


def fetch_fandom_page(url: str, delay: float = 1.0, retries: int = 3) -> Optional[str]:
    """
    Fetch a Fandom page using cloudscraper to bypass Cloudflare.
    """
    for attempt in range(1, retries + 1):
        try:
            time.sleep(delay)
            response = FANDOM_SCRAPER.get(url, timeout=30)
            
            # Check for 404 (wiki doesn't exist)
            if response.status_code == 404:
                logger.debug(f"Wiki not found: {url}")
                return None
            
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
    
    logger.debug(f"Failed to fetch {url} after {retries} attempts")
    return None


# ============== URL GENERATION ==============

def get_fandom_wiki_url(media_title: str) -> str:
    """
    Generate Fandom wiki URL for a media title.
    """
    wiki_name = media_title.lower()
    wiki_name = re.sub(r"['''\"`]", "", wiki_name)
    wiki_name = re.sub(r"[!?*.,;:&@#$%^()\[\]{}<>/\\|+=~\-]", "", wiki_name)
    wiki_name = wiki_name.replace(" ", "")
    return f"https://{wiki_name}.fandom.com"


def get_character_list_page(wiki_base: str) -> str:
    """Get URL for character list page."""
    return f"{wiki_base}/wiki/Category:Characters"


# ============== PARSING ==============

def parse_character_list(html: str, wiki_base: str) -> List[str]:
    """
    Parse character category page to get list of character page URLs.
    """
    soup = parse_html(html)
    character_urls = []
    
    # Fandom category pages list characters in a specific div
    category_content = soup.find('div', class_='category-page__members')
    if not category_content:
        category_content = soup.find('div', id='mw-pages')
    
    if category_content:
        for link in category_content.find_all('a'):
            href = link.get('href', '')
            if href.startswith('/wiki/') and ':' not in href:
                character_urls.append(f"{wiki_base}{href}")
    
    return character_urls


def parse_character_page(html: str, url: str) -> Optional[Dict]:
    """
    Parse a Fandom character page to extract personality and description.
    """
    soup = parse_html(html)
    
    # Get character name from page title
    title_elem = soup.find('h1', class_='page-header__title')
    if not title_elem:
        title_elem = soup.find('h1', id='firstHeading')
    
    if not title_elem:
        return None
    
    char_name = title_elem.get_text(strip=True)
    
    # Skip non-character pages
    skip_keywords = ['episode', 'season', 'list', 'category', 'transcript']
    if any(kw in char_name.lower() for kw in skip_keywords):
        return None
    
    # Extract personality section
    personality_text = ""
    for header in soup.find_all(['h2', 'h3']):
        header_text = header.get_text(strip=True).lower()
        if 'personality' in header_text or 'character' in header_text:
            content = []
            for sibling in header.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                if sibling.name == 'p':
                    content.append(sibling.get_text(strip=True))
            personality_text = ' '.join(content)
            break
    
    # Get introduction/first paragraphs
    intro_text = ""
    content_div = soup.find('div', class_='mw-parser-output')
    if content_div:
        first_paras = content_div.find_all('p', limit=3)
        intro_text = ' '.join(p.get_text(strip=True) for p in first_paras)
    
    # Extract actor from infobox
    actor_name = None
    infobox = soup.find('aside', class_='portable-infobox')
    if infobox:
        for row in infobox.find_all('div', class_='pi-item'):
            label = row.find('h3', class_='pi-data-label')
            value = row.find('div', class_='pi-data-value')
            if label and value:
                label_text = label.get_text(strip=True).lower()
                if 'actor' in label_text or 'portrayed' in label_text or 'played' in label_text:
                    actor_name = value.get_text(strip=True)
                    break
    
    full_description = f"{intro_text} {personality_text}".strip()
    
    if not full_description:
        return None
    
    return {
        "name": char_name,
        "actor_name": actor_name,
        "description": full_description[:3000],
        "personality_section": personality_text[:1500],
        "url": url,
        "source": "fandom"
    }


# ============== CRAWLING ==============

def crawl_fandom_for_title(media_title: str) -> Optional[Dict]:
    """
    Crawl Fandom wiki for a single media title.
    """
    wiki_base = get_fandom_wiki_url(media_title)
    char_list_url = get_character_list_page(wiki_base)
    
    logger.info(f"Crawling Fandom: {char_list_url}")
    
    html = fetch_fandom_page(char_list_url)
    if not html:
        return None
    
    character_urls = parse_character_list(html, wiki_base)
    
    if not character_urls:
        logger.debug(f"No character URLs found for {media_title}")
        return None
    
    logger.info(f"Found {len(character_urls)} characters for {media_title}")
    
    # Crawl individual character pages
    characters = []
    for url in character_urls[:50]:  # Limit to 50 characters per show
        html = fetch_fandom_page(url, delay=0.5)
        if html:
            char_data = parse_character_page(html, url)
            if char_data:
                char_data["media_title"] = media_title
                characters.append(char_data)
    
    if not characters:
        return None
    
    return {
        "media_title": media_title,
        "wiki_base": wiki_base,
        "characters": characters,
        "character_count": len(characters)
    }


def crawl_all_titles(titles: List[str], output_dir: Path = None) -> Dict:
    """Crawl Fandom for all titles."""
    if output_dir is None:
        output_dir = RAW_DIR / "fandom"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {"total": len(titles), "success": 0, "failed": 0, "skipped": 0, "characters": 0}
    
    for title in tqdm(titles, desc="Crawling Fandom"):
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Skip if already cached
        if output_file.exists():
            try:
                data = load_json(output_file)
                if data.get("characters"):
                    stats["skipped"] += 1
                    stats["characters"] += data.get("character_count", 0)
                    continue
            except:
                pass
        
        result = crawl_fandom_for_title(title)
        
        if result:
            save_json(result, output_file)
            stats["success"] += 1
            stats["characters"] += result["character_count"]
        else:
            stats["failed"] += 1
    
    return stats


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("FANDOM WIKI CRAWLER")
    print("="*60)
    
    if not TITLES_MASTER_FILE.exists():
        logger.error(f"Title list not found: {TITLES_MASTER_FILE}")
        logger.error("Run crawler_titles.py first!")
        return
    
    titles_data = load_json(TITLES_MASTER_FILE)
    titles = [t["title"] for t in titles_data]
    
    print(f"Loaded {len(titles)} titles")
    
    # Check cached
    output_dir = RAW_DIR / "fandom"
    cached = sum(1 for t in titles if (output_dir / f"{slugify(t)}.json").exists())
    
    print(f"Already cached: {cached}")
    print(f"Need to crawl:  {len(titles) - cached}")
    print("\nNote: Not all shows have Fandom wikis")
    print("Starting crawl...\n")
    
    stats = crawl_all_titles(titles)
    
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    print(f"Total titles:      {stats['total']}")
    print(f"Successful:        {stats['success']}")
    print(f"Failed:            {stats['failed']}")
    print(f"Skipped (cached):  {stats['skipped']}")
    print(f"Characters found:  {stats['characters']}")
    print("="*60)


if __name__ == "__main__":
    main()