import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
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
TVTROPES_TROPES= f"{TVTROPES_BASE}/pmwiki/pmwiki.php/Main"


def get_character_page_url(media_title: str) -> str:
    print(media_title)
    return f"{TVTROPES_TROPES}/{media_title}"

def crawl_tvtropes_for_trope(media_title: str) -> Optional[Dict]:
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
    
    soup = parse_html(html)
    main_div = soup.find("div", {"id": "main-article"})
    
    if main_div:
        paragraphs = main_div.find_all("p")
        body_txt = " ".join([p.get_text(separator=" ", strip=True) for p in paragraphs])
    else:
        body_txt = ""
        print(f"Main content not found for {media_title}")


    return {
        "trope_title": media_title,
        "url": url,
        "body_txt": body_txt
    }


def crawl_all_titles(titles: List[str], output_dir: Path = RAW_DIR / "tvtropes_tropes_redo") -> Dict:
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
        # slug = slugify(title)
        output_file = output_dir / f"{title}.json"
        
        # Skip if already crawled
        if output_file.exists():
            logger.info(f"Skipping {title} (already crawled)")
            data = load_json(output_file)
            stats["success"] += 1
            # stats["characters"] += data.get("character_count", 0)
            continue
        
        result = crawl_tvtropes_for_trope(title)
        
        if result:
            save_json(result, output_file)
            stats["success"] += 1
            # stats["characters"] += result["character_count"]
        else:
            stats["failed"] += 1
    
    logger.info(f"TVTropes crawl complete: {stats}")
    return stats


def main():
    chars_list = []
    tropes_list = []
    tvtropes = "/Users/alisongunzler/Desktop/FP_IWRA/WAandIRFinalProject/data/raw/tvtropes"
    for filename in os.listdir(tvtropes):
        # print(filename)
        if filename.endswith(".json"):
            with open(os.path.join(tvtropes, filename), "r") as f:
                df = pd.read_json(f)
                chars = df["characters"]
                for char in chars:
                    if char.get("name") !=  "open/close all folders":
                        tropes_list.extend(char["tropes"])
                
    # print(chars_list[0])
    print(tropes_list)
    tropes_list = set(tropes_list)
    tropes_list = list(tropes_list)
    
    # Load master title list
    titles = tropes_list
    # print(titles)
    stats = crawl_all_titles(titles)
    print(f"\nCrawl Summary: {stats}")

if __name__ == "__main__":
    main()