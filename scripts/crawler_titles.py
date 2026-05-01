# scripts/crawler_titles.py
"""
Build master title list from Wikiquote's list of television shows.

Sources:
- https://en.wikiquote.org/wiki/List_of_television_shows_(A–H)
- https://en.wikiquote.org/wiki/List_of_television_shows_(I–P)
- https://en.wikiquote.org/wiki/List_of_television_shows_(Q–Z)

Output: data/titles_master.json
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Set
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from shared.utils import fetch_page, parse_html, save_json, load_json, logger
from shared.config import DATA_DIR, TITLES_MASTER_FILE


WIKIQUOTE_TV_LISTS = [
    "https://en.wikiquote.org/wiki/List_of_television_shows_(A%E2%80%93H)",
    "https://en.wikiquote.org/wiki/List_of_television_shows_(I%E2%80%93P)",
    "https://en.wikiquote.org/wiki/List_of_television_shows_(Q%E2%80%93Z)",
]

# Additional movie lists from Wikiquote
WIKIQUOTE_FILM_LISTS = [
    "https://en.wikiquote.org/wiki/List_of_films_(A%E2%80%93B)",
    "https://en.wikiquote.org/wiki/List_of_films_(C%E2%80%93D)",
    "https://en.wikiquote.org/wiki/List_of_films_(E%E2%80%93G)",
    "https://en.wikiquote.org/wiki/List_of_films_(H%E2%80%93K)",
    "https://en.wikiquote.org/wiki/List_of_films_(L%E2%80%93N)",
    "https://en.wikiquote.org/wiki/List_of_films_(O%E2%80%93R)",
    "https://en.wikiquote.org/wiki/List_of_films_(S%E2%80%93T)",
    "https://en.wikiquote.org/wiki/List_of_films_(U%E2%80%93Z)",
]


def parse_wikiquote_list_page(html: str, media_type: str = "TV") -> List[Dict]:
    """
    Parse a Wikiquote list page to extract titles.
    
    Args:
        html: Raw HTML of the list page
        media_type: "TV" or "Movie"
    
    Returns:
        List of title dictionaries
    """
    soup = parse_html(html)
    titles = []
    seen_titles = set()
    
    # Find the main content div
    content = soup.find('div', class_='mw-parser-output')
    if not content:
        content = soup.find('div', id='mw-content-text')
    
    if not content:
        logger.warning("Could not find content div")
        return titles
    
    # Wikiquote lists titles in various formats:
    # 1. As links in lists (<ul><li><a>Title</a></li></ul>)
    # 2. As links in paragraphs
    # 3. Sometimes with year in parentheses
    
    # Method 1: Find all links that point to wikiquote pages (not external, not special pages)
    for link in content.find_all('a'):
        href = link.get('href', '')
        title_text = link.get_text(strip=True)
        
        # Skip empty, external links, special pages, and navigation
        if not title_text:
            continue
        if href.startswith('http') and 'wikiquote.org' not in href:
            continue
        if ':' in href and not href.startswith('/wiki/'):
            continue
        if any(skip in href.lower() for skip in ['special:', 'help:', 'category:', 'wikipedia:', 'template:', 'talk:']):
            continue
        if any(skip in title_text.lower() for skip in ['edit', '[', ']', 'citation', 'reference']):
            continue
        
        # Clean up the title
        title = clean_title(title_text)
        
        # Skip if too short or already seen
        if len(title) < 2:
            continue
        if title.lower() in seen_titles:
            continue
        
        # Try to extract year from surrounding text or title itself
        year = extract_year(title_text, link)
        
        # Clean title of year if it was in the title
        title = re.sub(r'\s*\(\d{4}[^)]*\)\s*$', '', title).strip()
        title = re.sub(r'\s*\d{4}\s*$', '', title).strip()
        
        if len(title) < 2:
            continue
            
        seen_titles.add(title.lower())
        
        titles.append({
            "title": title,
            "type": media_type,
            "year": year,
            "genres": [],
            "source": "wikiquote"
        })
    
    return titles


def clean_title(title: str) -> str:
    """Clean up a title string."""
    # Remove common suffixes/prefixes
    title = re.sub(r'\s*\(TV series\)\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(film\)\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(movie\)\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(American TV series\)\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(British TV series\)\s*', '', title, flags=re.IGNORECASE)
    
    # Remove brackets and their contents if they're disambiguation
    title = re.sub(r'\s*\([^)]*series[^)]*\)\s*', '', title, flags=re.IGNORECASE)
    
    # Clean whitespace
    title = ' '.join(title.split())
    
    return title.strip()


def extract_year(title_text: str, link_element) -> int:
    """Try to extract year from title text or surrounding context."""
    # Check in the title itself
    year_match = re.search(r'\((\d{4})\)', title_text)
    if year_match:
        return int(year_match.group(1))
    
    # Check in surrounding text (parent li or next sibling)
    parent = link_element.parent
    if parent:
        parent_text = parent.get_text()
        year_match = re.search(r'\((\d{4})', parent_text)
        if year_match:
            year = int(year_match.group(1))
            if 1950 <= year <= 2025:
                return year
    
    return None


def crawl_wikiquote_tv_lists() -> List[Dict]:
    """Crawl all Wikiquote TV show list pages."""
    all_titles = []
    
    for url in tqdm(WIKIQUOTE_TV_LISTS, desc="Crawling Wikiquote TV lists"):
        logger.info(f"Fetching: {url}")
        html = fetch_page(url, delay=1.0)
        
        if not html:
            logger.error(f"Failed to fetch {url}")
            continue
        
        titles = parse_wikiquote_list_page(html, media_type="TV")
        logger.info(f"Found {len(titles)} titles from {url}")
        all_titles.extend(titles)
    
    return all_titles


def crawl_wikiquote_film_lists() -> List[Dict]:
    """Crawl all Wikiquote film list pages."""
    all_titles = []
    
    for url in tqdm(WIKIQUOTE_FILM_LISTS, desc="Crawling Wikiquote film lists"):
        logger.info(f"Fetching: {url}")
        html = fetch_page(url, delay=1.0)
        
        if not html:
            logger.error(f"Failed to fetch {url}")
            continue
        
        titles = parse_wikiquote_list_page(html, media_type="Movie")
        logger.info(f"Found {len(titles)} titles from {url}")
        all_titles.extend(titles)
    
    return all_titles


def add_seed_titles() -> List[Dict]:
    """Add curated seed titles to ensure we have good coverage of popular shows."""
    return [
        # Popular sitcoms (ensure these are included)
        {"title": "Brooklyn Nine-Nine", "type": "TV", "year": 2013, "genres": ["Comedy", "Crime"], "source": "seed"},
        {"title": "The Office", "type": "TV", "year": 2005, "genres": ["Comedy"], "source": "seed"},
        {"title": "Parks and Recreation", "type": "TV", "year": 2009, "genres": ["Comedy"], "source": "seed"},
        {"title": "New Girl", "type": "TV", "year": 2011, "genres": ["Comedy", "Romance"], "source": "seed"},
        {"title": "Friends", "type": "TV", "year": 1994, "genres": ["Comedy", "Romance"], "source": "seed"},
        {"title": "Seinfeld", "type": "TV", "year": 1989, "genres": ["Comedy"], "source": "seed"},
        {"title": "How I Met Your Mother", "type": "TV", "year": 2005, "genres": ["Comedy", "Romance"], "source": "seed"},
        {"title": "The Good Place", "type": "TV", "year": 2016, "genres": ["Comedy", "Fantasy"], "source": "seed"},
        {"title": "Schitt's Creek", "type": "TV", "year": 2015, "genres": ["Comedy"], "source": "seed"},
        {"title": "Arrested Development", "type": "TV", "year": 2003, "genres": ["Comedy"], "source": "seed"},
        {"title": "Community", "type": "TV", "year": 2009, "genres": ["Comedy"], "source": "seed"},
        {"title": "30 Rock", "type": "TV", "year": 2006, "genres": ["Comedy"], "source": "seed"},
        {"title": "It's Always Sunny in Philadelphia", "type": "TV", "year": 2005, "genres": ["Comedy"], "source": "seed"},
        {"title": "Curb Your Enthusiasm", "type": "TV", "year": 2000, "genres": ["Comedy"], "source": "seed"},
        {"title": "Veep", "type": "TV", "year": 2012, "genres": ["Comedy"], "source": "seed"},
        {"title": "Silicon Valley", "type": "TV", "year": 2014, "genres": ["Comedy"], "source": "seed"},
        {"title": "Modern Family", "type": "TV", "year": 2009, "genres": ["Comedy"], "source": "seed"},
        {"title": "The Big Bang Theory", "type": "TV", "year": 2007, "genres": ["Comedy"], "source": "seed"},
        {"title": "Ted Lasso", "type": "TV", "year": 2020, "genres": ["Comedy", "Drama", "Sport"], "source": "seed"},
        {"title": "Abbott Elementary", "type": "TV", "year": 2021, "genres": ["Comedy"], "source": "seed"},
        {"title": "What We Do in the Shadows", "type": "TV", "year": 2019, "genres": ["Comedy", "Horror"], "source": "seed"},
        {"title": "Fleabag", "type": "TV", "year": 2016, "genres": ["Comedy", "Drama"], "source": "seed"},
        
        # Popular dramas
        {"title": "Breaking Bad", "type": "TV", "year": 2008, "genres": ["Drama", "Crime", "Thriller"], "source": "seed"},
        {"title": "Game of Thrones", "type": "TV", "year": 2011, "genres": ["Drama", "Fantasy"], "source": "seed"},
        {"title": "The Sopranos", "type": "TV", "year": 1999, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "The Wire", "type": "TV", "year": 2002, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "Mad Men", "type": "TV", "year": 2007, "genres": ["Drama"], "source": "seed"},
        {"title": "Stranger Things", "type": "TV", "year": 2016, "genres": ["Drama", "Fantasy", "Horror"], "source": "seed"},
        {"title": "The Crown", "type": "TV", "year": 2016, "genres": ["Drama", "History"], "source": "seed"},
        {"title": "Succession", "type": "TV", "year": 2018, "genres": ["Drama"], "source": "seed"},
        {"title": "Better Call Saul", "type": "TV", "year": 2015, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "Ozark", "type": "TV", "year": 2017, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "The Walking Dead", "type": "TV", "year": 2010, "genres": ["Drama", "Horror"], "source": "seed"},
        {"title": "Lost", "type": "TV", "year": 2004, "genres": ["Drama", "Mystery"], "source": "seed"},
        {"title": "Dexter", "type": "TV", "year": 2006, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "House", "type": "TV", "year": 2004, "genres": ["Drama", "Mystery"], "source": "seed"},
        {"title": "Grey's Anatomy", "type": "TV", "year": 2005, "genres": ["Drama", "Romance"], "source": "seed"},
        {"title": "The Mandalorian", "type": "TV", "year": 2019, "genres": ["Drama", "Sci-Fi"], "source": "seed"},
        {"title": "The Boys", "type": "TV", "year": 2019, "genres": ["Drama", "Action"], "source": "seed"},
        {"title": "Peaky Blinders", "type": "TV", "year": 2013, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "True Detective", "type": "TV", "year": 2014, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "Westworld", "type": "TV", "year": 2016, "genres": ["Drama", "Sci-Fi"], "source": "seed"},
        
        # Animated
        {"title": "The Simpsons", "type": "TV", "year": 1989, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "Family Guy", "type": "TV", "year": 1999, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "South Park", "type": "TV", "year": 1997, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "Rick and Morty", "type": "TV", "year": 2013, "genres": ["Animation", "Comedy", "Sci-Fi"], "source": "seed"},
        {"title": "BoJack Horseman", "type": "TV", "year": 2014, "genres": ["Animation", "Comedy", "Drama"], "source": "seed"},
        {"title": "Archer", "type": "TV", "year": 2009, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "Bob's Burgers", "type": "TV", "year": 2011, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "Futurama", "type": "TV", "year": 1999, "genres": ["Animation", "Comedy", "Sci-Fi"], "source": "seed"},
        {"title": "King of the Hill", "type": "TV", "year": 1997, "genres": ["Animation", "Comedy"], "source": "seed"},
        {"title": "American Dad", "type": "TV", "year": 2005, "genres": ["Animation", "Comedy"], "source": "seed"},
        
        # Popular movies
        {"title": "The Shawshank Redemption", "type": "Movie", "year": 1994, "genres": ["Drama"], "source": "seed"},
        {"title": "The Godfather", "type": "Movie", "year": 1972, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "Pulp Fiction", "type": "Movie", "year": 1994, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "Fight Club", "type": "Movie", "year": 1999, "genres": ["Drama"], "source": "seed"},
        {"title": "Forrest Gump", "type": "Movie", "year": 1994, "genres": ["Drama", "Romance"], "source": "seed"},
        {"title": "The Dark Knight", "type": "Movie", "year": 2008, "genres": ["Action", "Drama"], "source": "seed"},
        {"title": "Inception", "type": "Movie", "year": 2010, "genres": ["Sci-Fi", "Action"], "source": "seed"},
        {"title": "The Matrix", "type": "Movie", "year": 1999, "genres": ["Sci-Fi", "Action"], "source": "seed"},
        {"title": "Goodfellas", "type": "Movie", "year": 1990, "genres": ["Drama", "Crime"], "source": "seed"},
        {"title": "The Silence of the Lambs", "type": "Movie", "year": 1991, "genres": ["Thriller", "Horror"], "source": "seed"},
    ]


def deduplicate_titles(titles: List[Dict]) -> List[Dict]:
    """Remove duplicate titles, keeping the one with most info."""
    seen = {}
    
    for title_info in titles:
        title_lower = title_info["title"].lower().strip()
        
        # Skip very short or invalid titles
        if len(title_lower) < 2:
            continue
        
        if title_lower in seen:
            # Keep the one with more information (year, genres)
            existing = seen[title_lower]
            if title_info.get("year") and not existing.get("year"):
                seen[title_lower] = title_info
            elif title_info.get("genres") and not existing.get("genres"):
                seen[title_lower] = title_info
            elif title_info.get("source") == "seed":
                # Prefer seed titles as they have curated info
                seen[title_lower] = title_info
        else:
            seen[title_lower] = title_info
    
    return list(seen.values())


def build_master_title_list(include_films: bool = True) -> List[Dict]:
    """
    Build the master list of titles from Wikiquote.
    
    Args:
        include_films: Whether to also crawl film lists
    
    Returns:
        List of title dictionaries
    """
    all_titles = []
    
    # Add seed titles first
    seed = add_seed_titles()
    all_titles.extend(seed)
    logger.info(f"Added {len(seed)} seed titles")
    
    # Crawl TV shows from Wikiquote
    tv_titles = crawl_wikiquote_tv_lists()
    all_titles.extend(tv_titles)
    logger.info(f"Crawled {len(tv_titles)} TV titles from Wikiquote")
    
    # Optionally crawl films
    if include_films:
        film_titles = crawl_wikiquote_film_lists()
        all_titles.extend(film_titles)
        logger.info(f"Crawled {len(film_titles)} film titles from Wikiquote")
    
    # Deduplicate
    unique_titles = deduplicate_titles(all_titles)
    logger.info(f"After deduplication: {len(unique_titles)} unique titles")
    
    # Sort alphabetically
    unique_titles.sort(key=lambda x: x["title"].lower())
    
    # Save
    save_json(unique_titles, TITLES_MASTER_FILE)
    logger.info(f"Saved master title list to {TITLES_MASTER_FILE}")
    
    return unique_titles


def print_statistics(titles: List[Dict]) -> None:
    """Print statistics about the title list."""
    tv_count = sum(1 for t in titles if t.get("type") == "TV")
    movie_count = sum(1 for t in titles if t.get("type") == "Movie")
    with_year = sum(1 for t in titles if t.get("year"))
    with_genres = sum(1 for t in titles if t.get("genres"))
    
    print("\n" + "="*50)
    print("MASTER TITLE LIST STATISTICS")
    print("="*50)
    print(f"Total titles:     {len(titles)}")
    print(f"TV shows:         {tv_count}")
    print(f"Movies:           {movie_count}")
    print(f"With year:        {with_year} ({100*with_year/len(titles):.1f}%)")
    print(f"With genres:      {with_genres} ({100*with_genres/len(titles):.1f}%)")
    print("="*50)
    
    # Show sample
    print("\nSample titles:")
    for t in titles[:10]:
        year_str = f" ({t['year']})" if t.get('year') else ""
        print(f"  - {t['title']}{year_str} [{t['type']}]")
    print("  ...")


def main():
    """Main entry point."""
    print("Building master title list from Wikiquote...")
    
    # Build the list (set include_films=False to only get TV shows)
    titles = build_master_title_list(include_films=True)
    
    # Print statistics
    print_statistics(titles)
    
    print(f"\nTitle list saved to: {TITLES_MASTER_FILE}")


if __name__ == "__main__":
    main()