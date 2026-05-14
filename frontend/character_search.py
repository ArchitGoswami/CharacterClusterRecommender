# character_search.py
"""
Interactive CLI for finding similar characters based on TV Tropes data.
Uses questionary for arrow-key navigation.
"""

import os
import json
import pandas as pd
from collections import defaultdict

try:
    import questionary
    from questionary import Style
except ImportError:
    print("Please install questionary: pip install questionary")
    exit(1)

# === Custom Style ===
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:gray'),
    ('instruction', 'fg:gray'),
])

# === ANSI Color Codes ===
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def colored(text, color):
    """Wrap text in color codes."""
    return f"{color}{text}{Colors.RESET}"


# === Cluster Name Cleaning ===
def clean_cluster_name(raw_name):
    """
    Convert raw cluster names to readable format.
    'cluster_123_parents_parent_child' -> 'Parents / Parent / Child'
    """
    if raw_name == "No Cluster":
        return "Uncategorized"
    
    parts = raw_name.split('_')
    if len(parts) > 2 and parts[0] == 'cluster':
        words = parts[2:]
    else:
        words = parts
    
    cleaned = ' / '.join(word.capitalize() for word in words if word)
    return cleaned if cleaned else "Uncategorized"


# === Data Loading ===
def load_character_index(index_file="character_index.json"):
    """Load the pre-built character index."""
    if not os.path.exists(index_file):
        print(colored(f"\n Character index not found: {index_file}", Colors.RED))
        print(colored("   Run 'python build_character_index.py' first to build the index.\n", Colors.YELLOW))
        return None
    
    with open(index_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_clusters(cluster_dir="../FINAL_CLUSTERS/clustering_with_sep_title"):
    """Load all cluster data."""
    clusters = {}
    
    if not os.path.exists(cluster_dir):
        print(colored(f"\n  Cluster directory not found: {cluster_dir}", Colors.YELLOW))
        return clusters
    
    for filename in os.listdir(cluster_dir):
        if not filename.endswith(".txt"):
            continue

        cluster_name = filename.replace(".txt", "")
        if cluster_name == "cluster_-1_unclustered":
            cluster_name = "No Cluster"
        
        path = os.path.join(cluster_dir, filename)

        with open(path, "r", encoding="utf-8") as f:
            words = [
                line.strip()
                for i, line in enumerate(f)
                if i >= 2 and line.strip()
            ]
        
        for word in words:
            clusters[word] = cluster_name
    
    return clusters


def load_character_data(char_name, media_title, source_file, data_dir="../data/raw/tvtropes"):
    """Load full character data from the source JSON file."""
    filepath = os.path.join(data_dir, source_file)
    
    with open(filepath, "r", encoding="utf-8") as f:
        df = pd.read_json(f)
    
    chars = df["characters"]
    for char in chars:
        if char.get("name") == char_name and char.get("media_title") == media_title:
            return char
    
    return None


def load_all_characters(data_dir="../data/raw/tvtropes", exclude_char=None, exclude_media=None):
    """Load all characters for comparison."""
    chars_list = []
    
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            df = pd.read_json(f)
        
        if "characters" not in df.columns:
            continue
        
        chars = df["characters"]
        for char in chars:
            name = char.get("name", "")
            media = char.get("media_title", "")
            
            if name == "open/close all folders":
                continue
            
            if exclude_char and exclude_media:
                if name == exclude_char and media == exclude_media:
                    continue
            
            chars_list.append(char)
    
    return chars_list


# === Search Functions ===
def search_characters(query, character_index):
    """Search for characters matching the query."""
    query_lower = query.lower().strip()
    results = []
    
    if not query_lower:
        return results
    
    characters = character_index.get("characters", {})
    name_lookup = character_index.get("name_lookup", {})
    
    # Exact match
    if query_lower in name_lookup:
        for name in name_lookup[query_lower]:
            results.append((name, characters[name]))
    
    # Partial match
    for name, appearances in characters.items():
        if query_lower in name.lower() and (name, appearances) not in results:
            results.append((name, appearances))
    
    results.sort(key=lambda x: (-len(x[1]), x[0]))
    return results


def search_media(query, character_index):
    """Search for media/shows matching the query."""
    query_lower = query.lower().strip()
    results = []
    
    if not query_lower:
        return results
    
    media = character_index.get("media", {})
    media_lookup = character_index.get("media_lookup", {})
    
    # Exact match
    if query_lower in media_lookup:
        for title in media_lookup[query_lower]:
            results.append((title, media[title]))
    
    # Partial match
    for title, characters in media.items():
        if query_lower in title.lower() and (title, characters) not in results:
            results.append((title, characters))
    
    results.sort(key=lambda x: (-len(x[1]), x[0]))
    return results


# === Selection Functions using Questionary ===
def select_character_from_results(results):
    """
    Display character search results and let user select with arrow keys.
    Returns selected character dict or None.
    """
    if not results:
        return None
    
    # Build choices list
    choices = []
    selection_map = {}
    
    for name, appearances in results:
        for appearance in appearances:
            # Create display string
            display = f"{name} — {appearance['media_title']} ({appearance['trope_count']} tropes)"
            choices.append(display)
            selection_map[display] = {
                "name": name,
                "media_title": appearance["media_title"],
                "source_file": appearance["source_file"],
                "trope_count": appearance["trope_count"]
            }
    
    # Add back option
    choices.append("← Back to search")
    
    # Show selection prompt
    selected = questionary.select(
        "Select a character:",
        choices=choices,
        style=custom_style,
        instruction="(Use arrow keys to navigate, Enter to select)"
    ).ask()
    
    if selected is None or selected == "← Back to search":
        return None
    
    return selection_map[selected]


def select_media_from_results(results):
    """
    Display media search results and let user select with arrow keys.
    Returns selected media dict or None.
    """
    if not results:
        return None
    
    # Build choices list
    choices = []
    selection_map = {}
    
    for title, characters in results:
        display = f"{title} ({len(characters)} characters)"
        choices.append(display)
        selection_map[display] = {
            "media_title": title,
            "characters": characters
        }
    
    choices.append("← Back to search")
    
    selected = questionary.select(
        "Select a show/media:",
        choices=choices,
        style=custom_style,
        instruction="(Use arrow keys to navigate, Enter to select)"
    ).ask()
    
    if selected is None or selected == "← Back to search":
        return None
    
    return selection_map[selected]


def select_character_from_media(media_title, characters):
    """
    Display characters from a show and let user select with arrow keys.
    Returns selected character dict or None.
    """
    # Sort by trope count
    sorted_chars = sorted(characters, key=lambda x: -x.get("trope_count", 0))
    
    # Build choices
    choices = []
    selection_map = {}
    
    for char in sorted_chars:
        display = f"{char['name']} ({char['trope_count']} tropes)"
        choices.append(display)
        selection_map[display] = {
            "name": char["name"],
            "media_title": media_title,
            "source_file": char["source_file"],
            "trope_count": char["trope_count"]
        }
    
    choices.append("← Back to show selection")
    
    selected = questionary.select(
        f"Select a character from '{media_title}':",
        choices=choices,
        style=custom_style,
        instruction="(Use arrow keys to navigate, Enter to select)"
    ).ask()
    
    if selected is None or selected == "← Back to show selection":
        return None
    
    return selection_map[selected]


# === Similarity Calculation ===
def calculate_similarity(target_char, all_chars, clusters, weight_tropes=3, weight_clusters=1):
    """Calculate similarity scores for all characters."""
    target_tropes = set(target_char.get("tropes", []))
    target_clusters = set()
    
    for trope in target_tropes:
        cluster = clusters.get(trope, "No Cluster")
        if cluster != "No Cluster":
            target_clusters.add(cluster)
    
    results = []
    
    for char in all_chars:
        char_tropes = set(char.get("tropes", []))
        char_clusters = set()
        
        for trope in char_tropes:
            cluster = clusters.get(trope, "No Cluster")
            if cluster != "No Cluster":
                char_clusters.add(cluster)
        
        common_tropes = target_tropes & char_tropes
        common_clusters = target_clusters & char_clusters
        
        score = len(common_tropes) * weight_tropes + len(common_clusters) * weight_clusters
        
        if score > 0:
            results.append({
                "name": char.get("name"),
                "media_title": char.get("media_title"),
                "score": score,
                "common_tropes": list(common_tropes),
                "common_clusters": list(common_clusters),
                "trope_count": len(char_tropes)
            })
    
    results.sort(key=lambda x: (-x["score"], x["name"]))
    return results


# === Display Functions ===
def display_character_info(char_data, clusters):
    """Display information about the selected character."""
    name = char_data.get("name", "Unknown")
    media = char_data.get("media_title", "Unknown")
    tropes = char_data.get("tropes", [])
    
    print(colored("\n" + "═"*60, Colors.BLUE))
    print(colored(f"  {name}", Colors.BOLD))
    print(colored(f"  {media}", Colors.CYAN))
    print(colored(f"   {len(tropes)} tropes", Colors.DIM))
    print(colored("═"*60, Colors.BLUE))
    
    # Group tropes by cluster
    cluster_groups = defaultdict(list)
    for trope in tropes:
        cluster = clusters.get(trope, "No Cluster")
        cluster_groups[cluster].append(trope)
    
    print(colored("\nTropes by Category:\n", Colors.CYAN))
    
    for cluster, cluster_tropes in sorted(cluster_groups.items(), key=lambda x: -len(x[1])):
        clean_name = clean_cluster_name(cluster)
        print(colored(f"  {clean_name}", Colors.YELLOW) + colored(f" ({len(cluster_tropes)})", Colors.DIM))
        for trope in sorted(cluster_tropes)[:5]:
            print(f"    • {trope}")
        if len(cluster_tropes) > 5:
            print(colored(f"    ... and {len(cluster_tropes) - 5} more", Colors.DIM))
        print()


def display_similar_characters(similar_chars, top_n=5):
    """Display the most similar characters."""
    if not similar_chars:
        print(colored("\n No similar characters found.", Colors.RED))
        return
    
    print(colored(f"\n Top {top_n} Similar Characters:\n", Colors.GREEN))
    
    for i, char in enumerate(similar_chars[:top_n], 1):
        print(colored(f"{'─'*55}", Colors.DIM))
        
        # Rank and name
        rank_color = Colors.CYAN if i == 1 else Colors.DIM
        print(colored(f"  #{i}", rank_color) + colored(f"  {char['name']}", Colors.BOLD))
        print(colored(f"      from {char['media_title']}", Colors.DIM))
        print(colored(f"      Score: {char['score']}", Colors.GREEN))
        
        # Common tropes
        if char['common_tropes']:
            print(colored(f"\n      Common Tropes ({len(char['common_tropes'])}):", Colors.YELLOW))
            for trope in char['common_tropes'][:6]:
                print(f"        • {trope}")
            if len(char['common_tropes']) > 6:
                print(colored(f"        ... and {len(char['common_tropes']) - 6} more", Colors.DIM))
        
        # Common clusters
        if char['common_clusters']:
            print(colored(f"\n      Common Categories ({len(char['common_clusters'])}):", Colors.CYAN))
            for cluster in char['common_clusters'][:4]:
                print(f"        • {clean_cluster_name(cluster)}")
            if len(char['common_clusters']) > 4:
                print(colored(f"        ... and {len(char['common_clusters']) - 4} more", Colors.DIM))
        
        print()
    
    print(colored(f"{'─'*55}\n", Colors.DIM))


# === Main Menu ===
def get_search_mode():
    """Ask user what they want to search for."""
    choices = [
        "Search by character name",
        "Search by show/media title",
        "Help",
        "Exit"
    ]
    
    selected = questionary.select(
        "What would you like to do?",
        choices=choices,
        style=custom_style
    ).ask()
    
    if selected is None or "Exit" in selected:
        return "exit"
    elif "character" in selected:
        return "character"
    elif "show" in selected:
        return "media"
    elif "Help" in selected:
        return "help"
    
    return None


def display_help():
    """Display help information."""
    print(colored("""
╔══════════════════════════════════════════════════════════════╗
║                   CHARACTER SIMILARITY SEARCH                ║
║                         Help & Usage                         ║
╚══════════════════════════════════════════════════════════════╝
""", Colors.BLUE))
    
    print(colored("HOW TO USE:", Colors.BOLD))
    print("""
  1. Choose a search mode from the menu:
     • Search by character name - Find characters by name
     • Search by show/media - Browse characters in a show

  2. Enter your search term (partial matches work!)
     • "Jake" finds all Jakes
     • "Breaking" finds Breaking Bad, Breaking In, etc.

  3. Use arrow keys (↑↓) to navigate the results

  4. Press Enter to select

  5. View the character's tropes and similar characters
""")
    
    print(colored("NAVIGATION:", Colors.BOLD))
    print("""
  ↑ / ↓     Navigate through options
  Enter     Select current option
  Ctrl+C    Cancel / Go back
""")
    
    print(colored("SCORING:", Colors.BOLD))
    print("""
  Characters are ranked by:
  • Shared tropes (weighted 3x)
  • Shared trope categories (weighted 1x)
  
  Higher score = more similar character
""")
    
    input(colored("\nPress Enter to continue...", Colors.DIM))


# === Flow Handlers ===
def handle_character_search(character_index, clusters):
    """Handle character search flow."""
    
    # Get search query
    query = questionary.text(
        "Enter character name to search:",
        style=custom_style
    ).ask()
    
    if not query:
        return
    
    print(colored(f"\n Searching for '{query}'...\n", Colors.DIM))
    
    # Search
    results = search_characters(query, character_index)
    
    if not results:
        print(colored(f"No characters found matching '{query}'", Colors.RED))
        print(colored("Try a different spelling or partial name.\n", Colors.YELLOW))
        return
    
    # Count total matches
    total_matches = sum(len(appearances) for _, appearances in results)
    print(colored(f"Found {total_matches} character(s) matching '{query}'\n", Colors.GREEN))
    
    # Let user select
    selected = select_character_from_results(results)
    
    if selected is None:
        return
    
    process_selected_character(selected, clusters)


def handle_media_search(character_index, clusters):
    """Handle media/show search flow."""
    
    # Get search query
    query = questionary.text(
        "Enter show/media name to search:",
        style=custom_style
    ).ask()
    
    if not query:
        return
    
    print(colored(f"\n Searching for '{query}'...\n", Colors.DIM))
    
    # Search
    results = search_media(query, character_index)
    
    if not results:
        print(colored(f" No shows found matching '{query}'", Colors.RED))
        print(colored("   Try a different spelling or partial name.\n", Colors.YELLOW))
        return
    
    print(colored(f"Found {len(results)} show(s) matching '{query}'\n", Colors.GREEN))
    
    # Let user select a show
    selected_media = select_media_from_results(results)
    
    if selected_media is None:
        return
    
    # Let user select a character from that show
    selected_char = select_character_from_media(
        selected_media["media_title"],
        selected_media["characters"]
    )
    
    if selected_char is None:
        return
    
    process_selected_character(selected_char, clusters)


def process_selected_character(selected, clusters):
    """Process a selected character."""
    
    print(colored("\nLoading character data...", Colors.DIM))
    
    char_data = load_character_data(
        selected["name"],
        selected["media_title"],
        selected["source_file"]
    )
    
    if char_data is None:
        print(colored("Could not load character data.", Colors.RED))
        return
    
    # Display character info
    display_character_info(char_data, clusters)
    
    # Find similar characters
    print(colored("Finding similar characters...", Colors.DIM))
    
    all_chars = load_all_characters(
        exclude_char=selected["name"],
        exclude_media=selected["media_title"]
    )
    
    similar = calculate_similarity(char_data, all_chars, clusters)
    display_similar_characters(similar)
    
    # Pause before returning to menu
    input(colored("Press Enter to continue...", Colors.DIM))


# === Main Loop ===
def main():
    """Main interactive loop."""
    
    # Welcome banner
    print(colored("""
╔══════════════════════════════════════════════════════════════╗
║                  CHARACTER SIMILARITY SEARCH                 ║
║                    TV Tropes Analysis Tool                   ║
╚══════════════════════════════════════════════════════════════╝
""", Colors.BLUE))
    
    # Load data
    print(colored("Loading data...", Colors.DIM))
    
    character_index = load_character_index()
    if character_index is None:
        return
    
    clusters = load_clusters()
    
    metadata = character_index.get("metadata", {})
    print(colored(f" Loaded {metadata.get('unique_names', 0):,} unique characters", Colors.GREEN))
    print(colored(f" Loaded {metadata.get('unique_media', 0):,} unique shows/media", Colors.GREEN))
    print(colored(f" Loaded {len(clusters):,} trope-to-cluster mappings\n", Colors.GREEN))
    
    # Main loop
    while True:
        try:
            mode = get_search_mode()
            
            if mode == "exit":
                print(colored("\n Goodbye!\n", Colors.GREEN))
                break
            
            elif mode == "character":
                handle_character_search(character_index, clusters)
            
            elif mode == "media":
                handle_media_search(character_index, clusters)
            
            elif mode == "help":
                display_help()
        
        except KeyboardInterrupt:
            print(colored("\n", Colors.RESET))
            continue
        
        except Exception as e:
            print(colored(f"\nError: {e}\n", Colors.RED))


if __name__ == "__main__":
    main()