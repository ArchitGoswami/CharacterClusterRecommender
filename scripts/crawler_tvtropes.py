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


ARTICLES = {"the", "a", "an"}
NUMBER_WORDS = [
    "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen", "Twenty", "TwentyOne", "TwentyTwo",
    "TwentyThree", "TwentyFour", "TwentyFive", "TwentySix", "TwentySeven",
    "TwentyEight", "TwentyNine", "Thirty",
]


def spell_number_token(word: str) -> str:
    """TVTropes spells small numbers, so 24 becomes TwentyFour."""
    if word.isdigit() and int(word) < len(NUMBER_WORDS):
        return NUMBER_WORDS[int(word)]
    return word.capitalize()
WORK_NAMESPACES = {
    "Movie": ["Film", "Franchise"],
    "TV": ["Series", "WesternAnimation"],
}
REQUEST_DELAY = 0.4
MAX_SUBPAGES = 15
SKIP_SECTIONS = ("open/close all folders", "general tropes", "spoiler", "ymmv")


def candidate_slugs(media_title: str) -> List[str]:
    """TVTropes page slugs, including article-word variants like TheKingOfQueens."""
    cleaned = re.sub(r"\([^)]*\)", " ", media_title)
    cleaned = cleaned.replace("&", " and ")
    cleaned = cleaned.strip(" .")
    trailing = re.match(r"^(.*?),\s*(the|a|an)$", cleaned, re.IGNORECASE)
    forms = [cleaned]
    if trailing:
        forms.append(f"{trailing.group(2)} {trailing.group(1)}")

    slugs: List[str] = []
    for form in forms:
        words = re.findall(r"[A-Za-z0-9']+", form)
        if not words:
            continue
        camel = "".join(word.capitalize() for word in words).replace("'", "")
        spelled = "".join(spell_number_token(word) for word in words).replace("'", "")
        variants = [camel]
        if spelled != camel:
            variants.append(spelled)
        if words[0].lower() in ARTICLES and len(words) > 1:
            variants.append("".join(word.capitalize() for word in words[1:]).replace("'", ""))
        elif not camel.startswith("The"):
            variants.append(f"The{camel}")
        for variant in variants:
            if variant and variant not in slugs:
                slugs.append(variant)
    return slugs[:4]


def get_character_page_url(media_title: str) -> str:
    """Generate the most likely TVTropes character page URL for a media title."""
    slugs = candidate_slugs(media_title)
    slug = slugs[0] if slugs else "Unknown"
    return f"{TVTROPES_CHARACTERS}/{slug}"


def is_letter_bucket(name: str) -> bool:
    """True for trope indexes like A-B, which are not characters."""
    return bool(re.fullmatch(r"[A-Z](?:\s*[-–—]\s*[A-Z])?", (name or "").strip()))


def page_subject_name(soup) -> str:
    """Character name from a page whose folders are alphabetical trope groups."""
    heading = soup.select_one("h1")
    if not heading:
        return ""
    text = ""
    for child in heading.children:
        if getattr(child, "name", None) is None and str(child).strip():
            text = str(child).strip()
            break
    if not text:
        text = heading.get_text(" ", strip=True)
    if ":" in text:
        text = text.split(":")[-1].strip()
    text = re.sub(r"^Characters\s*/\s*", "", text).strip()
    if " - " in text:
        text = text.split(" - ")[-1].strip()
    text = re.sub(r"\s+\d+\s+Follow.*$", "", text).strip()
    return text


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
        lowered = char_name.lower()

        # Skip index controls and non-character sections
        if (
            not char_name
            or len(char_name) > 80
            or lowered in SKIP_SECTIONS
            or any(skip in lowered for skip in ['tropes', 'spoiler', 'ymmv'])
            or lowered.startswith('general')
        ):
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
                "tropes": list(dict.fromkeys(tropes)),
                "description": description[:2000],
                "source": "tvtropes"
            })

    buckets = [character for character in characters if is_letter_bucket(character["name"])]
    others = [character for character in characters if not is_letter_bucket(character["name"])]
    if len(buckets) >= 3 and len(buckets) > len(others):
        tropes = []
        descriptions = []
        for bucket in buckets:
            tropes.extend(bucket.get("tropes") or [])
            if bucket.get("description"):
                descriptions.append(bucket["description"])
        name = page_subject_name(soup)
        if name and tropes:
            others.append({
                "name": name,
                "media_title": media_title,
                "tropes": list(dict.fromkeys(tropes)),
                "description": " ".join(descriptions)[:2000],
                "source": "tvtropes",
            })
        return others

    return characters


def absolute_tvtropes_url(href: str) -> Optional[str]:
    """Turn a TVTropes href into an absolute URL, ignoring edit links."""
    href = href.split("?")[0].strip()
    if not href or "action=" in href:
        return None
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return f"{TVTROPES_BASE}{href}"
    return None


def subpage_urls(html: str, slug: str) -> List[str]:
    """Character subpages linked from a hub page, such as KimPossibleTeamPossible."""
    soup = parse_html(html)
    article = soup.select_one("#main-entry") or soup
    prefix = f"/Characters/{slug}"
    found: List[str] = []
    for link in article.find_all("a", href=True):
        url = absolute_tvtropes_url(link["href"])
        if not url or prefix not in url:
            continue
        if url.rstrip("/").endswith(f"/Characters/{slug}"):
            continue
        if url not in found:
            found.append(url)
    return found[:MAX_SUBPAGES]


def character_urls_from_work_page(slug: str, media_type: str = "TV") -> List[str]:
    """Find character pages linked from the show's main TVTropes article."""
    for namespace in WORK_NAMESPACES.get(media_type, WORK_NAMESPACES["TV"]):
        url = f"{TVTROPES_BASE}/pmwiki/pmwiki.php/{namespace}/{slug}"
        html = fetch_page(url, delay=REQUEST_DELAY)
        if not html:
            continue
        soup = parse_html(html)
        article = soup.select_one("#main-entry") or soup
        found: List[str] = []
        for link in article.find_all("a", href=True):
            absolute = absolute_tvtropes_url(link["href"])
            if absolute and "/Characters/" in absolute and absolute not in found:
                found.append(absolute)
        return found[:MAX_SUBPAGES]
    return []


def dedupe_characters(characters: List[Dict]) -> List[Dict]:
    """Keep the richest entry when a subpage repeats a character."""
    best: Dict[str, Dict] = {}
    for character in characters:
        name = character.get("name", "").strip()
        if not name or is_letter_bucket(name):
            continue
        key = name.lower()
        current = best.get(key)
        if current is None or len(character.get("tropes", [])) > len(current.get("tropes", [])):
            best[key] = character
    return list(best.values())


def characters_from_pages(urls: List[str], media_title: str) -> List[Dict]:
    """Parse character folders from each page URL."""
    characters: List[Dict] = []
    for url in urls:
        html = fetch_page(url, delay=REQUEST_DELAY)
        if html:
            characters.extend(parse_character_page(html, media_title))
    return characters


def crawl_tvtropes_for_title(media_title: str, media_type: str = "TV") -> Optional[Dict]:
    """
    Crawl TVTropes for a single media title.

    Hub pages that only link to character subpages are followed. If the
    guessed Characters URL 404s, alternate slugs and the show article are tried.
    """
    slugs = candidate_slugs(media_title)
    characters: List[Dict] = []
    used_url = None

    for slug in slugs:
        url = f"{TVTROPES_CHARACTERS}/{slug}"
        logger.info(f"Crawling TVTropes: {url}")
        html = fetch_page(url, delay=REQUEST_DELAY)
        if not html:
            continue
        used_url = url
        page_characters = parse_character_page(html, media_title)
        subpages = subpage_urls(html, slug)
        if subpages:
            logger.info(f"{media_title}: following {len(subpages)} character subpages")
            page_characters.extend(characters_from_pages(subpages, media_title))
        characters = dedupe_characters(page_characters)
        if characters:
            break

    if not characters and slugs:
        work_links = character_urls_from_work_page(slugs[0], media_type)
        if work_links:
            logger.info(f"{media_title}: found {len(work_links)} character links on the work page")
            characters = dedupe_characters(characters_from_pages(work_links, media_title))
            used_url = work_links[0]

    if not characters:
        logger.warning(f"No characters found for {media_title}")
        return None

    return {
        "media_title": media_title,
        "url": used_url,
        "characters": characters,
        "character_count": len(characters)
    }


def crawl_all_titles(titles: List[Dict], output_dir: Path = RAW_DIR / "tvtropes") -> Dict:
    """
    Crawl TVTropes for all titles in the list.
    
    Args:
        titles: List of media titles to crawl
        output_dir: Directory to save raw data
    
    Returns:
        Summary statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {"total": len(titles), "success": 0, "failed": 0, "characters": 0, "failed_titles": []}
    
    for entry in tqdm(titles, desc="Crawling TVTropes"):
        title = entry["title"] if isinstance(entry, dict) else entry
        media_type = entry.get("type", "TV") if isinstance(entry, dict) else "TV"
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Skip if already crawled
        if output_file.exists():
            logger.debug(f"Skipping {title} (already crawled)")
            data = load_json(output_file)
            stats["success"] += 1
            stats["characters"] += data.get("character_count", 0)
            continue
        
        result = crawl_tvtropes_for_title(title, media_type)
        
        if result:
            save_json(result, output_file)
            stats["success"] += 1
            stats["characters"] += result["character_count"]
        else:
            stats["failed"] += 1
            stats["failed_titles"].append(title)

    summary = {key: value for key, value in stats.items() if key != "failed_titles"}
    logger.info(f"TVTropes crawl complete: {summary}")
    if stats["failed_titles"]:
        save_json(stats["failed_titles"], output_dir.parent / "tvtropes_failed.json")
    return stats


def refresh_existing(output_dir: Path = RAW_DIR / "tvtropes") -> Dict:
    """Pull character subpages for shows crawled before hub pages were followed."""
    import subprocess
    root = output_dir.parent.parent.parent
    tracked = subprocess.check_output(
        ["git", "ls-files", "data/raw/tvtropes"],
        cwd=root,
        text=True,
    ).splitlines()
    stats = {"checked": 0, "updated": 0, "added": 0}
    for relative in tracked:
        path = root / relative
        if not path.exists():
            continue
        data = load_json(path)
        url = data.get("url") or ""
        if "/Characters/" not in url:
            continue
        slug = url.rstrip("/").split("/Characters/")[-1]
        html = fetch_page(url, delay=REQUEST_DELAY)
        stats["checked"] += 1
        if not html:
            continue
        media_title = data.get("media_title") or path.stem
        fresh = parse_character_page(html, media_title)
        subpages = subpage_urls(html, slug)
        if subpages:
            logger.info(f"{media_title}: refreshing {len(subpages)} subpages")
            fresh.extend(characters_from_pages(subpages, media_title))
        merged = dedupe_characters((data.get("characters") or []) + fresh)
        added = len(merged) - len(data.get("characters") or [])
        if added > 0:
            data["characters"] = merged
            data["character_count"] = len(merged)
            save_json(data, path)
            stats["updated"] += 1
            stats["added"] += added
            logger.info(f"{media_title}: added {added} characters")
    logger.info(f"Refresh complete: {stats}")
    return stats


def repair_letter_buckets(output_dir: Path = RAW_DIR / "tvtropes") -> Dict:
    """Re-read pages that stored A-B style trope groups as if they were characters."""
    stats = {"checked": 0, "updated": 0}
    for path in sorted(output_dir.glob("*.json")):
        data = load_json(path)
        characters = data.get("characters") or []
        if not any(is_letter_bucket(character.get("name", "")) for character in characters):
            continue
        url = data.get("url") or ""
        if "/Characters/" not in url:
            continue
        stats["checked"] += 1
        slug = url.rstrip("/").split("/Characters/")[-1]
        html = fetch_page(url, delay=REQUEST_DELAY)
        if not html:
            continue
        media_title = data.get("media_title") or path.stem
        fresh = parse_character_page(html, media_title)
        subpages = subpage_urls(html, slug)
        if subpages:
            fresh.extend(characters_from_pages(subpages, media_title))
        kept = [character for character in characters if not is_letter_bucket(character.get("name", ""))]
        merged = dedupe_characters(kept + fresh)
        if merged != characters:
            data["characters"] = merged
            data["character_count"] = len(merged)
            save_json(data, path)
            stats["updated"] += 1
            logger.info(f"{media_title}: repaired to {len(merged)} characters")
    logger.info(f"Repair complete: {stats}")
    return stats


def main():
    """Main entry point for TVTropes crawler."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    if args.repair:
        stats = repair_letter_buckets()
        print(f"Repair summary: {stats}")
        return
    if args.refresh:
        stats = refresh_existing()
        print(f"Refresh summary: {stats}")
        return

    # Load master title list
    if TITLES_MASTER_FILE.exists():
        titles_data = load_json(TITLES_MASTER_FILE)
        titles = titles_data[args.shard::args.shards] if args.shards > 1 else titles_data
        logger.info(f"Shard {args.shard + 1}/{args.shards}: {len(titles)} titles")
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