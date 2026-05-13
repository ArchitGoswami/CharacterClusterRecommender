# character_search.py
"""
Interactive CLI for finding similar characters based on TV Tropes data.
"""

import os
import json
import pandas as pd
from collections import defaultdict

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

def bold(text):
    return colored(text, Colors.BOLD)

def dim(text):
    return colored(text, Colors.DIM)


# === Cluster Name Cleaning ===
def clean_cluster_name(raw_name):
    """
    Convert raw cluster names to readable format.
    'cluster_123_parents_parent_child' -> 'Parents / Parent / Child'
    """
    if raw_name == "No Cluster":
        return "Uncategorized"
    
    # Remove 'cluster_' prefix and number
    parts = raw_name.split('_')
    if len(parts) > 2 and parts[0] == 'cluster':
        # Skip 'cluster' and the number
        words = parts[2:]
    else:
        words = parts
    
    # Capitalize and join
    cleaned = ' / '.join(word.capitalize() for word in words if word)
    return cleaned if cleaned else "Uncategorized"


# === Character Index Loading ===
def load_character_index(index_file="character_index.json"):
    """Load the pre-built character index."""
    if not os.path.exists(index_file):
        print(colored(f"\n❌ Character index not found: {index_file}", Colors.RED))
        print(colored("   Run 'python build_character_index.py' first to build the index.\n", Colors.YELLOW))
        return None
    
    with open(index_file, "r", encoding="utf-8") as f:
        return json.load(f)


# === Cluster Loading ===
def load_clusters(cluster_dir="../FINAL_CLUSTERS/clustering_with_sep_title"):
    """Load all cluster data."""
    clusters = {}
    
    if not os.path.exists(cluster_dir):
        print(colored(f"\n⚠️  Cluster directory not found: {cluster_dir}", Colors.YELLOW))
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


# === Search Functions ===
def search_characters(query, character_index):
    """
    Search for characters matching the query.
    Returns list of (name, appearances) tuples.
    """
    query_lower = query.lower().strip()
    results = []
    
    if not query_lower:
        return results
    
    characters = character_index.get("characters", {})
    name_lookup = character_index.get("name_lookup", {})
    
    # Exact match in lookup
    if query_lower in name_lookup:
        for name in name_lookup[query_lower]:
            results.append((name, characters[name]))
    
    # Partial match - name contains query
    for name, appearances in characters.items():
        if query_lower in name.lower() and (name, appearances) not in results:
            results.append((name, appearances))
    
    # Sort by number of appearances (more appearances = more notable character)
    results.sort(key=lambda x: (-len(x[1]), x[0]))
    
    return results


def search_media(query, character_index):
    """
    Search for media/shows matching the query.
    Returns list of (media_title, characters) tuples.
    """
    query_lower = query.lower().strip()
    results = []
    
    if not query_lower:
        return results
    
    media = character_index.get("media", {})
    media_lookup = character_index.get("media_lookup", {})
    
    # Exact match in lookup
    if query_lower in media_lookup:
        for title in media_lookup[query_lower]:
            results.append((title, media[title]))
    
    # Partial match - title contains query
    for title, characters in media.items():
        if query_lower in title.lower() and (title, characters) not in results:
            results.append((title, characters))
    
    # Sort by number of characters (more characters = more notable show)
    results.sort(key=lambda x: (-len(x[1]), x[0]))
    
    return results


def display_search_results(results, query, max_display=20, search_type="character"):
    """Display search results and let user select."""
    
    if not results:
        print(colored(f"\n❌ No {search_type}s found matching '{query}'", Colors.RED))
        print(colored("   Try a different spelling or a partial name.\n", Colors.DIM))
        return None, None
    
    print(colored(f"\n📋 Found {len(results)} {search_type}(s) matching '{query}':\n", Colors.GREEN))
    
    # Flatten results for selection
    selection_list = []
    display_count = 0
    
    for item, details in results:
        if display_count >= max_display:
            remaining = len(results) - display_count
            print(colored(f"\n   ... and {remaining} more. Refine your search for better results.", Colors.DIM))
            break
        
        if search_type == "character":
            for appearance in details:
                display_count += 1
                selection_list.append({
                    "name": item,
                    "media_title": appearance["media_title"],
                    "source_file": appearance["source_file"],
                    "trope_count": appearance["trope_count"]
                })
                
                # Format the display
                idx = colored(f"[{display_count}]", Colors.CYAN)
                char_name = colored(item, Colors.BOLD)
                media = colored(f"from {appearance['media_title']}", Colors.DIM)
                tropes = colored(f"({appearance['trope_count']} tropes)", Colors.DIM)
                
                print(f"  {idx} {char_name} {media} {tropes}")
                
                if display_count >= max_display:
                    break
        else:  # search_type == "media"
            display_count += 1
            selection_list.append({
                "media_title": item,
                "characters": details,
                "character_count": len(details)
            })
            
            # Format the display
            idx = colored(f"[{display_count}]", Colors.CYAN)
            media_name = colored(item, Colors.BOLD)
            char_count = colored(f"({len(details)} characters)", Colors.DIM)
            
            print(f"  {idx} {media_name} {char_count}")
    
    return selection_list, len(results)


def display_media_characters(media_title, characters, max_display=30):
    """Display characters from a selected media/show."""
    
    print(colored(f"\n🎬 Characters in '{media_title}':\n", Colors.MAGENTA))
    
    # Sort by trope count (most developed characters first)
    sorted_chars = sorted(characters, key=lambda x: -x.get("trope_count", 0))
    
    selection_list = []
    
    for i, char in enumerate(sorted_chars[:max_display], 1):
        selection_list.append({
            "name": char["name"],
            "media_title": media_title,
            "source_file": char["source_file"],
            "trope_count": char["trope_count"]
        })
        
        idx = colored(f"[{i}]", Colors.CYAN)
        char_name = colored(char["name"], Colors.BOLD)
        tropes = colored(f"({char['trope_count']} tropes)", Colors.DIM)
        
        print(f"  {idx} {char_name} {tropes}")
    
    if len(sorted_chars) > max_display:
        print(colored(f"\n   ... and {len(sorted_chars) - max_display} more characters.", Colors.DIM))
    
    return selection_list


def get_selection(selection_list, prompt="Enter number to select (or 'b' to go back): "):
    """Prompt user to select from the list."""
    
    if not selection_list:
        return None
    
    print()
    while True:
        try:
            choice = input(colored(prompt, Colors.YELLOW)).strip()
            
            if choice.lower() == 'b':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(selection_list):
                return selection_list[idx]
            else:
                print(colored(f"  Please enter a number between 1 and {len(selection_list)}", Colors.RED))
        
        except ValueError:
            print(colored("  Please enter a valid number or 'b' to go back", Colors.RED))


# === Character Data Loading ===
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
            
            # Skip folder markers
            if name == "open/close all folders":
                continue
            
            # Skip the target character
            if exclude_char and exclude_media:
                if name == exclude_char and media == exclude_media:
                    continue
            
            chars_list.append(char)
    
    return chars_list


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
        
        # Calculate overlaps (using sets to avoid duplicates)
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
    
    # Sort by score descending
    results.sort(key=lambda x: (-x["score"], x["name"]))
    
    return results


# === Display Functions ===
def display_character_info(char_data, clusters):
    """Display information about the selected character."""
    
    name = char_data.get("name", "Unknown")
    media = char_data.get("media_title", "Unknown")
    tropes = char_data.get("tropes", [])
    
    print(colored("\n" + "="*60, Colors.BLUE))
    print(colored(f"  Selected Character: {name}", Colors.BOLD))
    print(colored(f"  From: {media}", Colors.DIM))
    print(colored(f"  Tropes: {len(tropes)}", Colors.DIM))
    print(colored("="*60 + "\n", Colors.BLUE))
    
    # Show tropes grouped by cluster
    cluster_groups = defaultdict(list)
    for trope in tropes:
        cluster = clusters.get(trope, "No Cluster")
        cluster_groups[cluster].append(trope)
    
    print(colored("📚 Tropes by Category:", Colors.CYAN))
    for cluster, cluster_tropes in sorted(cluster_groups.items()):
        clean_name = clean_cluster_name(cluster)
        print(f"\n  {colored(clean_name, Colors.YELLOW)} ({len(cluster_tropes)})")
        for trope in sorted(cluster_tropes)[:5]:  # Show max 5 per cluster
            print(f"    • {trope}")
        if len(cluster_tropes) > 5:
            print(colored(f"    ... and {len(cluster_tropes) - 5} more", Colors.DIM))


def display_similar_characters(similar_chars, top_n=5):
    """Display the most similar characters."""
    
    if not similar_chars:
        print(colored("\n❌ No similar characters found.", Colors.RED))
        return
    
    print(colored(f"\n🎭 Top {top_n} Similar Characters:\n", Colors.GREEN))
    
    for i, char in enumerate(similar_chars[:top_n], 1):
        # Header
        print(colored(f"{'─'*50}", Colors.DIM))
        rank = colored(f"#{i}", Colors.CYAN + Colors.BOLD)
        name = colored(char['name'], Colors.BOLD)
        media = colored(f"from {char['media_title']}", Colors.DIM)
        score = colored(f"Score: {char['score']}", Colors.GREEN)
        
        print(f"{rank} {name} {media}")
        print(f"   {score}")
        
        # Common tropes
        if char['common_tropes']:
            print(colored(f"\n   Common Tropes ({len(char['common_tropes'])}):", Colors.YELLOW))
            for trope in char['common_tropes'][:8]:
                print(f"     • {trope}")
            if len(char['common_tropes']) > 8:
                print(colored(f"     ... and {len(char['common_tropes']) - 8} more", Colors.DIM))
        
        # Common clusters
        if char['common_clusters']:
            print(colored(f"\n   Common Categories ({len(char['common_clusters'])}):", Colors.CYAN))
            for cluster in char['common_clusters'][:5]:
                print(f"     • {clean_cluster_name(cluster)}")
            if len(char['common_clusters']) > 5:
                print(colored(f"     ... and {len(char['common_clusters']) - 5} more", Colors.DIM))
        
        print()
    
    print(colored(f"{'─'*50}\n", Colors.DIM))


# === Help Display ===
def display_help():
    """Display help information."""
    
    print(colored("""
╔══════════════════════════════════════════════════════════════╗
║                   CHARACTER SIMILARITY SEARCH                 ║
║                         Help & Usage                          ║
╚══════════════════════════════════════════════════════════════╝
""", Colors.BLUE))
    
    print(colored("SEARCH MODES:", Colors.BOLD))
    print("  • " + colored("char <name>", Colors.CYAN) + "  - Search by character name (default)")
    print("  • " + colored("show <name>", Colors.CYAN) + "  - Search by show/media title")
    print()
    
    print(colored("EXAMPLES:", Colors.BOLD))
    print("  • " + colored("Jake", Colors.GREEN) + "           - Find all characters named Jake")
    print("  • " + colored("char Jake", Colors.GREEN) + "      - Same as above (explicit)")
    print("  • " + colored("show Breaking", Colors.GREEN) + "  - Find shows with 'Breaking' in title")
    print("  • " + colored("show Avatar", Colors.GREEN) + "    - Find Avatar and related shows")
    print()
    
    print(colored("COMMANDS:", Colors.BOLD))
    print("  • 'help' or '?' - Show this help message")
    print("  • 'quit' or 'exit' - Exit the program")
    print()
    
    print(colored("NAVIGATION:", Colors.BOLD))
    print("  • Enter a number to select from a list")
    print("  • Enter 'b' to go back to search")
    print()
    
    print(colored("SEARCH TIPS:", Colors.BOLD))
    print("  • Partial names work: 'Jake' finds all Jakes")
    print("  • Case-insensitive: 'JAKE' = 'jake' = 'Jake'")
    print("  • For shows, try partial titles: 'Breaking' for Breaking Bad")
    print()
    
    print(colored("SCORING:", Colors.BOLD))
    print("  • Characters are ranked by shared tropes and categories")
    print("  • Higher score = more similar character")
    print()


# === Main Search Mode Handler ===
def handle_character_search(query, character_index, clusters):
    """Handle character search flow."""
    
    results = search_characters(query, character_index)
    selection_list, total_count = display_search_results(results, query, search_type="character")
    
    if not selection_list:
        return
    
    # Let user select a character
    selected = get_selection(selection_list)
    
    if selected is None:
        return
    
    process_selected_character(selected, clusters)


def handle_show_search(query, character_index, clusters):
    """Handle show/media search flow."""
    
    results = search_media(query, character_index)
    selection_list, total_count = display_search_results(results, query, search_type="media")
    
    if not selection_list:
        return
    
    # Let user select a show
    selected_show = get_selection(selection_list, "Enter number to select show (or 'b' to go back): ")
    
    if selected_show is None:
        return
    
    # Display characters in the show
    char_list = display_media_characters(
        selected_show["media_title"],
        selected_show["characters"]
    )
    
    # Let user select a character from the show
    selected_char = get_selection(char_list, "Enter number to select character (or 'b' to go back): ")
    
    if selected_char is None:
        return
    
    process_selected_character(selected_char, clusters)


def process_selected_character(selected, clusters):
    """Process a selected character - load data, display info, find similar."""
    
    # Load full character data
    print(colored("\n⏳ Loading character data...", Colors.DIM))
    char_data = load_character_data(
        selected["name"],
        selected["media_title"],
        selected["source_file"]
    )
    
    if char_data is None:
        print(colored("❌ Could not load character data.", Colors.RED))
        return
    
    # Display character info
    display_character_info(char_data, clusters)
    
    # Find similar characters
    print(colored("⏳ Finding similar characters...", Colors.DIM))
    all_chars = load_all_characters(
        exclude_char=selected["name"],
        exclude_media=selected["media_title"]
    )
    
    similar = calculate_similarity(char_data, all_chars, clusters)
    display_similar_characters(similar)


# === Main Loop ===
def main():
    """Main interactive loop."""
    
    # Print welcome banner
    print(colored("""
╔══════════════════════════════════════════════════════════════╗
║               🎭 CHARACTER SIMILARITY SEARCH 🎭               ║
║                    TV Tropes Analysis Tool                    ║
╚══════════════════════════════════════════════════════════════╝
""", Colors.BLUE))
    
    # Load data
    print(colored("Loading data...", Colors.DIM))
    
    character_index = load_character_index()
    if character_index is None:
        return
    
    clusters = load_clusters()
    
    metadata = character_index.get("metadata", {})
    print(colored(f"✓ Loaded {metadata.get('unique_names', 0):,} unique characters", Colors.GREEN))
    print(colored(f"✓ Loaded {metadata.get('unique_media', 0):,} unique shows/media", Colors.GREEN))
    print(colored(f"✓ Loaded {len(clusters):,} trope-to-cluster mappings\n", Colors.GREEN))
    
    print(colored("Type 'help' for usage information.", Colors.DIM))
    print(colored("Search by character name, or use 'show <name>' to search by show.\n", Colors.DIM))
    
    # Main loop
    while True:
        try:
            user_input = input(colored("🔍 Search: ", Colors.CYAN)).strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ('quit', 'exit', 'q'):
                print(colored("\n👋 Goodbye!\n", Colors.GREEN))
                break
            
            if user_input.lower() in ('help', '?'):
                display_help()
                continue
            
            # Parse search mode
            parts = user_input.split(maxsplit=1)
            
            if len(parts) >= 2 and parts[0].lower() in ('show', 'media', 's'):
                # Show search mode
                query = parts[1]
                handle_show_search(query, character_index, clusters)
            
            elif len(parts) >= 2 and parts[0].lower() in ('char', 'character', 'c'):
                # Explicit character search mode
                query = parts[1]
                handle_character_search(query, character_index, clusters)
            
            else:
                # Default: character search
                query = user_input
                handle_character_search(query, character_index, clusters)
            
        except KeyboardInterrupt:
            print(colored("\n\n👋 Goodbye!\n", Colors.GREEN))
            break
        except Exception as e:
            print(colored(f"\n❌ Error: {e}\n", Colors.RED))


if __name__ == "__main__":
    main()