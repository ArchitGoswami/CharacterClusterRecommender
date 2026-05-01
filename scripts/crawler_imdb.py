# scripts/crawler_imdb.py
"""
IMDb data crawler using OMDB API.

OMDB API provides:
- Title search
- IMDb IDs
- Cast information (limited)
- Genres, year, plot, ratings

Get your free API key at: http://www.omdbapi.com/apikey.aspx
Free tier: 1,000 requests/day

Owner: Archit
Phase: 1 (Days 1-2)

Output: 
- data/raw/imdb/{title_slug}.json
- Updates data/titles_master.json with IMDb IDs
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from shared.utils import save_json, load_json, slugify, logger
from shared.config import RAW_DIR, TITLES_MASTER_FILE, DATA_DIR, TITLES_MASTER_TEST_FILE


# ============== CONFIGURATION ==============

# Set your OMDB API key here or as environment variable
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "852c0a30")

OMDB_BASE_URL = "http://www.omdbapi.com/"

# Rate limiting
REQUESTS_PER_DAY = 1000  # Free tier limit
REQUEST_DELAY = 0.5  # Seconds between requests


# ============== OMDB API FUNCTIONS ==============

def search_omdb(title: str, media_type: str = None, year: int = None) -> Optional[Dict]:
    """
    Search OMDB for a title.
    
    Args:
        title: Title to search for
        media_type: "movie", "series", or None for any
        year: Optional year to narrow search
    
    Returns:
        OMDB response dict or None if not found
    """
    if OMDB_API_KEY == "YOUR_API_KEY_HERE":
        logger.error("Please set your OMDB API key!")
        logger.error("Get one free at: http://www.omdbapi.com/apikey.aspx")
        logger.error("Set it in the script or as environment variable OMDB_API_KEY")
        return None
    
    params = {
        "apikey": OMDB_API_KEY,
        "t": title,  # Search by title (returns best match)
        "plot": "short"
    }
    
    # Add type filter if specified
    if media_type:
        if media_type.upper() == "TV":
            params["type"] = "series"
        elif media_type.upper() == "MOVIE":
            params["type"] = "movie"
    
    # Add year if specified
    if year:
        params["y"] = str(year)
    
    try:
        response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Response") == "True":
            return data
        else:
            # Try without year constraint if it failed
            if year and "Error" in data:
                del params["y"]
                response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
                data = response.json()
                if data.get("Response") == "True":
                    return data
            
            logger.debug(f"OMDB: No results for '{title}': {data.get('Error', 'Unknown error')}")
            return None
            
    except requests.RequestException as e:
        logger.warning(f"OMDB request failed for '{title}': {e}")
        return None


def get_omdb_by_id(imdb_id: str) -> Optional[Dict]:
    """
    Get detailed info from OMDB by IMDb ID.
    
    Args:
        imdb_id: IMDb ID (e.g., "tt0386676")
    
    Returns:
        OMDB response dict or None
    """
    if OMDB_API_KEY == "YOUR_API_KEY_HERE":
        return None
    
    params = {
        "apikey": OMDB_API_KEY,
        "i": imdb_id,
        "plot": "full"
    }
    
    try:
        response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Response") == "True":
            return data
        return None
        
    except requests.RequestException as e:
        logger.warning(f"OMDB request failed for ID '{imdb_id}': {e}")
        return None


def parse_omdb_response(omdb_data: Dict, original_title: str) -> Dict:
    """
    Parse OMDB response into our standard format.
    
    Args:
        omdb_data: Raw OMDB API response
        original_title: Original title we searched for
    
    Returns:
        Standardized title info dict
    """
    # Parse year (handles "2005–2013" format for TV series)
    year_str = omdb_data.get("Year", "")
    year_start = None
    year_end = None
    
    if year_str:
        year_match = year_str.split("–")  # Note: this is an en-dash, not hyphen
        if not year_match or len(year_match) == 1:
            year_match = year_str.split("-")
        
        try:
            year_start = int(year_match[0]) if year_match[0].isdigit() else None
            if len(year_match) > 1 and year_match[1].isdigit():
                year_end = int(year_match[1])
        except (ValueError, IndexError):
            pass
    
    # Parse genres
    genres = []
    if omdb_data.get("Genre"):
        genres = [g.strip() for g in omdb_data["Genre"].split(",")]
    
    # Determine media type
    omdb_type = omdb_data.get("Type", "").lower()
    if omdb_type == "series":
        media_type = "TV"
    elif omdb_type == "movie":
        media_type = "Movie"
    else:
        media_type = "Unknown"
    
    # Parse actors (OMDB gives comma-separated string)
    actors = []
    if omdb_data.get("Actors") and omdb_data["Actors"] != "N/A":
        actors = [a.strip() for a in omdb_data["Actors"].split(",")]
    
    return {
        "title": omdb_data.get("Title", original_title),
        "original_query": original_title,
        "imdb_id": omdb_data.get("imdbID"),
        "type": media_type,
        "year": year_start,
        "year_end": year_end,
        "genres": genres,
        "plot": omdb_data.get("Plot", "") if omdb_data.get("Plot") != "N/A" else "",
        "actors": actors,
        "director": omdb_data.get("Director", "") if omdb_data.get("Director") != "N/A" else "",
        "rated": omdb_data.get("Rated", ""),
        "runtime": omdb_data.get("Runtime", ""),
        "imdb_rating": omdb_data.get("imdbRating", ""),
        "poster_url": omdb_data.get("Poster", "") if omdb_data.get("Poster") != "N/A" else "",
        "source": "omdb"
    }


# ============== CRAWLING FUNCTIONS ==============

def crawl_title(title_info: Dict) -> Optional[Dict]:
    """
    Crawl OMDB for a single title.
    
    Args:
        title_info: Dict with at least "title" key, optionally "type" and "year"
    
    Returns:
        Enriched title info or None
    """
    title = title_info.get("title", "")
    media_type = title_info.get("type")
    year = title_info.get("year")
    
    if not title:
        return None
    
    # Search OMDB
    omdb_data = search_omdb(title, media_type, year)
    
    if omdb_data:
        result = parse_omdb_response(omdb_data, title)
        
        # Preserve any existing data that OMDB didn't provide
        if not result.get("genres") and title_info.get("genres"):
            result["genres"] = title_info["genres"]
        
        return result
    
    return None


def crawl_all_titles(titles: List[Dict], output_dir: Path = None, limit: int = None) -> Dict:
    """
    Crawl OMDB for all titles.
    
    Args:
        titles: List of title dicts from master list
        output_dir: Directory to save individual results
        limit: Optional limit for testing
    
    Returns:
        Statistics dict
    """
    if output_dir is None:
        output_dir = RAW_DIR / "imdb"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total": len(titles),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "with_imdb_id": 0,
        "with_actors": 0
    }
    
    enriched_titles = []
    titles_to_crawl = []
    
    # ============== PRE-CHECK: Skip already cached titles ==============
    print("\nChecking for cached data...")
    
    for title_info in titles:
        title = title_info.get("title", "")
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Check if we already have cached data for this title
        if output_file.exists():
            try:
                cached = load_json(output_file)
                
                # Verify it has valid data (not just an empty or failed result)
                if cached.get("imdb_id"):
                    enriched_titles.append(cached)
                    stats["skipped"] += 1
                    stats["with_imdb_id"] += 1
                    if cached.get("actors"):
                        stats["with_actors"] += 1
                    continue
            except Exception as e:
                logger.debug(f"Could not load cached file for '{title}': {e}")
        
        # Check if title_info already has imdb_id (from previous enrichment)
        if title_info.get("imdb_id"):
            enriched_titles.append(title_info)
            stats["skipped"] += 1
            stats["with_imdb_id"] += 1
            if title_info.get("actors"):
                stats["with_actors"] += 1
            continue
        
        # This title needs to be crawled
        titles_to_crawl.append(title_info)
    
    print(f"Already cached: {stats['skipped']}")
    print(f"Need to fetch:  {len(titles_to_crawl)}")
    
    # ============== APPLY LIMIT TO UNCACHED TITLES ONLY ==============
    if limit:
        titles_to_crawl = titles_to_crawl[:limit]
        print(f"Limited to:     {len(titles_to_crawl)} (limit={limit})")
    
    if not titles_to_crawl:
        print("\nAll titles already cached! Nothing to do.")
        return stats
    
    # ============== CRAWL UNCACHED TITLES ==============
    print(f"\nFetching {len(titles_to_crawl)} titles from OMDB...")
    
    for title_info in tqdm(titles_to_crawl, desc="Fetching from OMDB"):
        title = title_info.get("title", "")
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Crawl from OMDB
        result = crawl_title(title_info)
        
        if result and result.get("imdb_id"):
            save_json(result, output_file)
            enriched_titles.append(result)
            stats["success"] += 1
            stats["with_imdb_id"] += 1
            
            if result.get("actors"):
                stats["with_actors"] += 1
        else:
            # Keep original info even if OMDB lookup failed
            # Save a marker so we don't retry immediately
            failed_result = {
                **title_info,
                "omdb_lookup_failed": True,
                "source": "omdb_failed"
            }
            save_json(failed_result, output_file)
            enriched_titles.append(title_info)
            stats["failed"] += 1
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    # Update stats total to reflect only what we processed
    stats["total"] = stats["skipped"] + stats["success"] + stats["failed"]
    
    # Save updated master list with IMDb IDs
    save_enriched_master_list(enriched_titles)
    
    return stats

def save_enriched_master_list(titles: List[Dict]) -> None:
    """Save the enriched title list back to master file."""
    # Create backup of original
    backup_file = DATA_DIR / "titles_master_backup.json"
    if TITLES_MASTER_FILE.exists() and not backup_file.exists():
        original = load_json(TITLES_MASTER_FILE)
        save_json(original, backup_file)
        logger.info(f"Backed up original titles to {backup_file}")
    
    # Save enriched version
    save_json(titles, TITLES_MASTER_FILE)
    logger.info(f"Updated {TITLES_MASTER_FILE} with OMDB data")


# ============== MAIN ==============

def check_api_key() -> bool:
    """Check if API key is configured."""
    if OMDB_API_KEY == "YOUR_API_KEY_HERE":
        print("\n" + "="*60)
        print("OMDB API KEY REQUIRED")
        print("="*60)
        print("\n1. Get a free API key at: http://www.omdbapi.com/apikey.aspx")
        print("   (Free tier: 1,000 requests/day)")
        print("\n2. Set your API key by either:")
        print("   a) Edit this file and replace 'YOUR_API_KEY_HERE'")
        print("   b) Set environment variable: OMDB_API_KEY=your_key_here")
        print("\n" + "="*60)
        return False
    
    # Test the API key
    test_result = search_omdb("The Office")
    if test_result:
        logger.info("API key validated successfully")
        return True
    else:
        print("\nAPI key may be invalid or expired. Please check.")
        return False


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("OMDB CRAWLER - Fetching IMDb data")
    print("="*60)
    
    # Check API key
    if not check_api_key():
        return
    
    # Load titles
    if not TITLES_MASTER_FILE.exists():
        logger.error(f"Title list not found: {TITLES_MASTER_FILE}")
        logger.error("Run crawler_titles.py first!")
        return
    
    titles = load_json(TITLES_MASTER_FILE)
    logger.info(f"Loaded {len(titles)} titles")
    
    # Count how many already have IMDb IDs
    already_have = sum(1 for t in titles if t.get("imdb_id"))
    print(f"\nTitles already with IMDb ID: {already_have}")
    print(f"Titles to look up: {len(titles) - already_have}")
    
    # Warn about rate limits
    print(f"\nNote: Free tier allows {REQUESTS_PER_DAY} requests/day")
    print("Starting with first 100 titles (remove limit to do all)")
    
    # Crawl (with limit for safety)
    stats = crawl_all_titles(titles, limit=800)  # Remove limit=100 to do all
    
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    print(f"Total processed:   {stats['total']}")
    print(f"Successful:        {stats['success']}")
    print(f"Failed:            {stats['failed']}")
    print(f"Skipped (cached):  {stats['skipped']}")
    print(f"With IMDb ID:      {stats['with_imdb_id']}")
    print(f"With actors:       {stats['with_actors']}")
    print("="*60)
    
    print(f"\nData saved to: {RAW_DIR / 'imdb'}")
    print(f"Master list updated: {TITLES_MASTER_FILE}")


if __name__ == "__main__":
    main()