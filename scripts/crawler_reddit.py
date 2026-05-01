# scripts/crawler_reddit.py
"""
Reddit crawler for character discussions and personality descriptions.

Searches subreddits for character discussion threads and extracts
personality-related keywords and descriptions from comments.

Owner: Archit
Phase: 1 (Days 1-2)

Data sources:
- Show-specific subreddits (r/brooklynninenine, r/DunderMifflin, etc.)
- General TV subreddits (r/television, r/sitcoms)
- Character discussion threads

Output: data/raw/reddit/{media_slug}.json
"""

import re
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Set
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from shared.utils import save_json, load_json, slugify, logger
from shared.config import RAW_DIR, TITLES_MASTER_FILE


# ============== CONFIGURATION ==============

# Reddit API (no auth needed for public read-only access via .json endpoint)
REDDIT_BASE = "https://www.reddit.com"

# Rate limiting - Reddit is strict!
REQUEST_DELAY = 2.0  # seconds between requests

# Headers to avoid 429 errors
REDDIT_HEADERS = {
    "User-Agent": "CharacterPersonalityResearch/1.0 (Academic Project; Contact: student@university.edu)"
}

# Known subreddit mappings for popular shows
SUBREDDIT_MAP = {
    "brooklyn nine-nine": ["brooklynninenine", "b99"],
    "the office": ["DunderMifflin", "theoffice"],
    "parks and recreation": ["PandR", "parksandrec"],
    "friends": ["friends_tv_show", "howyoudoin"],
    "seinfeld": ["seinfeld"],
    "how i met your mother": ["HIMYM"],
    "the good place": ["TheGoodPlace"],
    "schitt's creek": ["SchittsCreek"],
    "arrested development": ["arresteddevelopment"],
    "community": ["community"],
    "30 rock": ["30ROCK"],
    "it's always sunny in philadelphia": ["IASIP"],
    "curb your enthusiasm": ["curb"],
    "veep": ["Veep"],
    "silicon valley": ["SiliconValleyHBO"],
    "modern family": ["Modern_Family"],
    "the big bang theory": ["bigbangtheory"],
    "breaking bad": ["breakingbad"],
    "game of thrones": ["gameofthrones", "freefolk"],
    "the sopranos": ["thesopranos"],
    "the wire": ["TheWire"],
    "mad men": ["madmen"],
    "stranger things": ["StrangerThings"],
    "the crown": ["TheCrownNetflix"],
    "succession": ["SuccessionTV"],
    "better call saul": ["betterCallSaul"],
    "ozark": ["Ozark"],
    "the walking dead": ["thewalkingdead"],
    "lost": ["lost"],
    "dexter": ["Dexter"],
    "the simpsons": ["TheSimpsons"],
    "family guy": ["familyguy"],
    "south park": ["southpark"],
    "rick and morty": ["rickandmorty"],
    "bojack horseman": ["BoJackHorseman"],
    "archer": ["ArcherFX"],
    "futurama": ["futurama"],
    "ted lasso": ["TedLasso"],
    "the mandalorian": ["TheMandalorianTV"],
    "the boys": ["TheBoys"],
    "fleabag": ["Fleabag"],
    "what we do in the shadows": ["WhatWeDointheShadows"],
}

# Search queries for finding character discussions
CHARACTER_SEARCH_QUERIES = [
    "{character} personality",
    "{character} character analysis",
    "{character} traits",
    "{character} why is",
    "{character} best moments",
    "{character} character development",
    "favorite thing about {character}",
    "unpopular opinion {character}",
]

# Personality-related keywords to look for in comments
PERSONALITY_KEYWORDS = [
    # Positive traits
    "kind", "funny", "smart", "intelligent", "brave", "loyal", "honest",
    "caring", "sweet", "charming", "witty", "clever", "confident", "humble",
    "generous", "patient", "calm", "wise", "creative", "passionate",
    
    # Negative traits
    "selfish", "arrogant", "rude", "mean", "lazy", "stupid", "annoying",
    "manipulative", "jealous", "petty", "immature", "naive", "stubborn",
    "cowardly", "dishonest", "cruel", "cold", "boring", "pretentious",
    
    # Neutral/descriptive
    "sarcastic", "awkward", "quirky", "eccentric", "intense", "reserved",
    "loud", "quiet", "serious", "goofy", "competitive", "ambitious",
    "perfectionist", "anxious", "dramatic", "mysterious", "complex",
]


# ============== REDDIT API FUNCTIONS ==============

def reddit_request(url: str, params: Dict = None) -> Optional[Dict]:
    """
    Make a request to Reddit's JSON API.
    
    Args:
        url: Reddit URL (will append .json)
        params: Query parameters
    
    Returns:
        JSON response or None
    """
    # Add .json to get JSON response
    if not url.endswith('.json'):
        url = url.rstrip('/') + '.json'
    
    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=30)
        
        if response.status_code == 429:
            logger.warning("Rate limited by Reddit. Waiting 60 seconds...")
            time.sleep(60)
            response = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=30)
        
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.warning(f"Reddit request failed for {url}: {e}")
        return None


def search_subreddit(subreddit: str, query: str, limit: int = 25) -> List[Dict]:
    """
    Search a subreddit for posts matching a query.
    
    Args:
        subreddit: Subreddit name (without r/)
        query: Search query
        limit: Max results
    
    Returns:
        List of post data
    """
    url = f"{REDDIT_BASE}/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "on",  # Restrict to this subreddit
        "sort": "relevance",
        "limit": limit,
        "t": "all"  # All time
    }
    
    data = reddit_request(url, params)
    
    if not data or "data" not in data:
        return []
    
    posts = []
    for child in data["data"].get("children", []):
        post = child.get("data", {})
        if post:
            posts.append({
                "title": post.get("title", ""),
                "selftext": post.get("selftext", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "permalink": post.get("permalink", ""),
                "id": post.get("id", ""),
            })
    
    return posts


def get_post_comments(permalink: str, limit: int = 100) -> List[str]:
    """
    Get comments from a Reddit post.
    
    Args:
        permalink: Post permalink (e.g., /r/sub/comments/id/title/)
        limit: Max comments to retrieve
    
    Returns:
        List of comment texts
    """
    url = f"{REDDIT_BASE}{permalink}.json"
    params = {"limit": limit, "sort": "top"}
    
    data = reddit_request(url, params)
    
    if not data or len(data) < 2:
        return []
    
    comments = []
    
    def extract_comments(node):
        """Recursively extract comments."""
        if isinstance(node, dict):
            if node.get("kind") == "t1":  # Comment
                body = node.get("data", {}).get("body", "")
                if body and body != "[deleted]" and body != "[removed]":
                    comments.append(body)
                
                # Get replies
                replies = node.get("data", {}).get("replies", "")
                if isinstance(replies, dict):
                    extract_comments(replies)
            
            elif node.get("kind") == "Listing":
                for child in node.get("data", {}).get("children", []):
                    extract_comments(child)
        
        elif isinstance(node, list):
            for item in node:
                extract_comments(item)
    
    extract_comments(data[1])  # data[1] contains comments
    
    return comments[:limit]


def extract_personality_mentions(text: str, character_name: str) -> Dict:
    """
    Extract personality-related mentions from text.
    
    Args:
        text: Comment or post text
        character_name: Character name to look for
    
    Returns:
        Dict with found traits and relevant sentences
    """
    text_lower = text.lower()
    char_lower = character_name.lower()
    char_first_name = char_lower.split()[0] if ' ' in char_lower else char_lower
    
    found_traits = []
    relevant_sentences = []
    
    # Check if character is mentioned
    if char_lower not in text_lower and char_first_name not in text_lower:
        return {"traits": [], "sentences": []}
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Check if sentence mentions character
        if char_lower in sentence_lower or char_first_name in sentence_lower:
            # Look for personality keywords
            for keyword in PERSONALITY_KEYWORDS:
                if keyword in sentence_lower:
                    found_traits.append(keyword)
                    if sentence.strip() and len(sentence) < 500:
                        relevant_sentences.append(sentence.strip())
                    break
    
    return {
        "traits": list(set(found_traits)),
        "sentences": list(set(relevant_sentences))[:10]
    }


# ============== CRAWLING FUNCTIONS ==============

def get_subreddits_for_title(title: str) -> List[str]:
    """
    Get list of subreddits to search for a title.
    """
    title_lower = title.lower()
    
    # Check known mappings
    if title_lower in SUBREDDIT_MAP:
        return SUBREDDIT_MAP[title_lower]
    
    # Generate guesses
    guesses = []
    
    # Remove common prefixes
    clean_title = title_lower
    for prefix in ["the ", "a "]:
        if clean_title.startswith(prefix):
            clean_title = clean_title[len(prefix):]
    
    # Try various formats
    guesses.append(clean_title.replace(" ", "").replace("'", "").replace("-", ""))
    guesses.append(clean_title.replace(" ", "_"))
    guesses.append(clean_title.replace(" ", ""))
    
    return list(set(guesses))


def crawl_reddit_for_title(media_title: str, known_characters: List[str] = None) -> Optional[Dict]:
    """
    Crawl Reddit for character discussions about a media title.
    
    Args:
        media_title: Name of show/movie
        known_characters: List of character names (from TVTropes/Fandom)
    
    Returns:
        Dict with character personality data
    """
    subreddits = get_subreddits_for_title(media_title)
    
    if not subreddits:
        logger.warning(f"No subreddits found for {media_title}")
        return None
    
    all_character_data = {}
    posts_processed = 0
    
    for subreddit in subreddits:
        logger.info(f"Searching r/{subreddit} for {media_title}")
        
        # If we have known characters, search for each
        if known_characters:
            for char_name in known_characters[:20]:  # Limit to top 20 characters
                for query_template in CHARACTER_SEARCH_QUERIES[:3]:  # Limit queries
                    query = query_template.format(character=char_name)
                    posts = search_subreddit(subreddit, query, limit=10)
                    
                    for post in posts:
                        posts_processed += 1
                        
                        # Extract from post title and body
                        post_text = f"{post['title']} {post['selftext']}"
                        mentions = extract_personality_mentions(post_text, char_name)
                        
                        # Get comments if post has enough engagement
                        if post['num_comments'] > 5:
                            comments = get_post_comments(post['permalink'], limit=50)
                            for comment in comments:
                                comment_mentions = extract_personality_mentions(comment, char_name)
                                mentions['traits'].extend(comment_mentions['traits'])
                                mentions['sentences'].extend(comment_mentions['sentences'])
                        
                        # Store results
                        if mentions['traits']:
                            char_key = char_name.lower()
                            if char_key not in all_character_data:
                                all_character_data[char_key] = {
                                    "name": char_name,
                                    "traits": [],
                                    "sentences": [],
                                    "post_count": 0
                                }
                            
                            all_character_data[char_key]['traits'].extend(mentions['traits'])
                            all_character_data[char_key]['sentences'].extend(mentions['sentences'])
                            all_character_data[char_key]['post_count'] += 1
        
        else:
            # General search for character discussions
            queries = ["character", "personality", "favorite character", "best character"]
            for query in queries:
                posts = search_subreddit(subreddit, query, limit=25)
                posts_processed += len(posts)
                # Process posts...
    
    if not all_character_data:
        logger.warning(f"No character data found for {media_title}")
        return None
    
    # Aggregate and clean results
    characters = []
    for char_key, data in all_character_data.items():
        # Count trait frequencies
        trait_counts = {}
        for trait in data['traits']:
            trait_counts[trait] = trait_counts.get(trait, 0) + 1
        
        # Sort by frequency
        sorted_traits = sorted(trait_counts.items(), key=lambda x: x[1], reverse=True)
        
        characters.append({
            "name": data['name'],
            "media_title": media_title,
            "traits": [t[0] for t in sorted_traits[:20]],  # Top 20 traits
            "trait_counts": dict(sorted_traits[:20]),
            "sample_sentences": list(set(data['sentences']))[:10],
            "post_count": data['post_count'],
            "source": "reddit"
        })
    
    return {
        "media_title": media_title,
        "subreddits_searched": subreddits,
        "posts_processed": posts_processed,
        "characters": characters,
        "character_count": len(characters)
    }


def get_known_characters(media_title: str) -> List[str]:
    """
    Get known characters from already-crawled TVTropes/Fandom data.
    """
    characters = []
    
    slug = slugify(media_title)
    
    # Check TVTropes
    tvtropes_file = RAW_DIR / "tvtropes" / f"{slug}.json"
    if tvtropes_file.exists():
        try:
            data = load_json(tvtropes_file)
            for char in data.get("characters", []):
                name = char.get("name", "")
                if name and len(name) > 1:
                    characters.append(name)
        except:
            pass
    
    # Check Fandom
    fandom_file = RAW_DIR / "fandom" / f"{slug}.json"
    if fandom_file.exists():
        try:
            data = load_json(fandom_file)
            for char in data.get("characters", []):
                name = char.get("name", "")
                if name and len(name) > 1 and name not in characters:
                    characters.append(name)
        except:
            pass
    
    return characters


def crawl_all_titles(titles: List[str], output_dir: Path = None, limit: int = None) -> Dict:
    """
    Crawl Reddit for all titles.
    """
    if output_dir is None:
        output_dir = RAW_DIR / "reddit"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if limit:
        titles = titles[:limit]
    
    stats = {
        "total": len(titles),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "characters": 0
    }
    
    for title in tqdm(titles, desc="Crawling Reddit"):
        slug = slugify(title)
        output_file = output_dir / f"{slug}.json"
        
        # Skip if cached
        if output_file.exists():
            try:
                data = load_json(output_file)
                if data.get("characters"):
                    stats["skipped"] += 1
                    stats["characters"] += data.get("character_count", 0)
                    continue
            except:
                pass
        
        # Get known characters from other crawlers
        known_chars = get_known_characters(title)
        
        if not known_chars:
            logger.debug(f"No known characters for {title}, skipping Reddit crawl")
            stats["failed"] += 1
            continue
        
        # Crawl Reddit
        result = crawl_reddit_for_title(title, known_chars)
        
        if result and result.get("characters"):
            save_json(result, output_file)
            stats["success"] += 1
            stats["characters"] += result["character_count"]
        else:
            stats["failed"] += 1
    
    return stats


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("REDDIT CRAWLER - Character Personality Discussions")
    print("="*60)
    
    if not TITLES_MASTER_FILE.exists():
        logger.error(f"Title list not found: {TITLES_MASTER_FILE}")
        return
    
    titles_data = load_json(TITLES_MASTER_FILE)
    titles = [t["title"] for t in titles_data]
    
    print(f"Loaded {len(titles)} titles")
    
    # Check which have TVTropes/Fandom data (Reddit needs character names)
    titles_with_chars = []
    for title in titles:
        chars = get_known_characters(title)
        if chars:
            titles_with_chars.append(title)
    
    print(f"Titles with known characters: {len(titles_with_chars)}")
    
    # Check cached
    output_dir = RAW_DIR / "reddit"
    cached = sum(1 for t in titles_with_chars if (output_dir / f"{slugify(t)}.json").exists())
    
    print(f"Already cached: {cached}")
    print(f"Need to crawl:  {len(titles_with_chars) - cached}")
    print("\nNote: Reddit rate limits are strict - this may take a while")
    print("Starting crawl...\n")
    
    # Start with popular shows that have known subreddits
    priority_titles = [t for t in titles_with_chars if t.lower() in SUBREDDIT_MAP]
    other_titles = [t for t in titles_with_chars if t.lower() not in SUBREDDIT_MAP]
    
    print(f"Priority titles (known subreddits): {len(priority_titles)}")
    
    # Crawl priority titles first
    stats = crawl_all_titles(priority_titles + other_titles, limit=50)  # Start with limit
    
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    print(f"Total processed:   {stats['total']}")
    print(f"Successful:        {stats['success']}")
    print(f"Failed:            {stats['failed']}")
    print(f"Skipped (cached):  {stats['skipped']}")
    print(f"Characters found:  {stats['characters']}")
    print("="*60)


if __name__ == "__main__":
    main()