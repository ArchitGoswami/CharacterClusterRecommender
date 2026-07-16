import json
import os
import re
from pathlib import Path
from collections import defaultdict

def load_character_index():
    """Load the character index."""
    with open('character_index.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_raw_character_data(show_file):
    """Load raw character data from tvtropes JSON file."""
    raw_path = Path('../data/raw/tvtropes') / show_file
    with open(raw_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_safe_filename(name):
    """Create a safe filename from a character name - always lowercase."""
    # Replace apostrophes and special characters with underscores
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Collapse multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Strip leading/trailing underscores, limit length, and LOWERCASE
    safe_name = safe_name.strip('_')[:50].lower()
    return safe_name

def process_characters():
    """Process all characters and create web-friendly data files."""
    print("Loading character index...")
    index = load_character_index()
    
    # Create output directory
    output_dir = Path('web_data')
    chars_dir = output_dir / 'characters'
    output_dir.mkdir(exist_ok=True)
    chars_dir.mkdir(exist_ok=True)
    
    # Clear existing character files to avoid stale data
    for old_file in chars_dir.glob('*.json'):
        old_file.unlink()
    print("Cleared old character files")
    
    # Create simplified index
    web_index = {
        'characters': {},
        'shows': defaultdict(list)
    }
    
    # Track created files to avoid duplicates
    created_files = set()
    
    # Process each character
    char_count = 0
    skipped_count = 0
    duplicate_count = 0
    
    for char_name, char_list in index['characters'].items():
        if not char_list:
            continue
            
        # Take first entry (handles multi-show characters)
        char_info = char_list[0]
        show_name = char_info['media_title']
        source_file = char_info['source_file']
        
        # Load raw character data
        try:
            raw_data = load_raw_character_data(source_file)
        except FileNotFoundError:
            print(f"Warning: Source file not found for {char_name}: {source_file}")
            skipped_count += 1
            continue
        
        # Find character in raw data
        char_data = None
        for character in raw_data.get('characters', []):
            if character.get('name') == char_name:
                char_data = character
                break
            if character.get('name', '').lower() == char_name.lower():
                char_data = character
                break
        
        if not char_data:
            for character in raw_data.get('characters', []):
                if char_name.lower() in character.get('name', '').lower():
                    char_data = character
                    break
        
        if not char_data:
            print(f"Warning: Character not found in raw data: {char_name} in {source_file}")
            skipped_count += 1
            continue
        
        tropes = char_data.get('tropes', [])
        
        if not tropes:
            skipped_count += 1
            continue
        
        tropes_by_category = {}
        
        # Get show ID (filename without extension) - already lowercase
        show_id = source_file.replace('.json', '')
        
        # Create safe character name - always lowercase
        safe_char_name = create_safe_filename(char_name)

        # Full character ID - all lowercase
        char_id = f"{show_id}_{safe_char_name}"
        char_filename = f"{char_id}.json"
        
        # Check for duplicate filenames
        if char_filename in created_files:
            suffix = 2
            while f"{char_id}_{suffix}.json" in created_files:
                suffix += 1
            char_id = f"{char_id}_{suffix}"
            char_filename = f"{char_id}.json"
            duplicate_count += 1

        created_files.add(char_filename)

        # Save individual character file
        char_file_data = {
            'name': char_name,
            'show': show_name,
            'trope_count': len(tropes),
            'tropes': tropes,
            'tropes_by_category': tropes_by_category
        }

        char_file_path = chars_dir / char_filename
        with open(char_file_path, 'w', encoding='utf-8') as f:
            json.dump(char_file_data, f, indent=2, ensure_ascii=False)

        # Add to web index - ID is lowercase to match filename
        web_index['characters'][char_name] = {
            'show': show_name,
            'trope_count': len(tropes),
            'id': char_id
        }

        web_index['shows'][show_name].append({
            'name': char_name,
            'trope_count': len(tropes),
            'id': char_id
        })
        
        char_count += 1
        if char_count % 100 == 0:
            print(f"Processed {char_count} characters...")
    
    # Convert defaultdict to regular dict for JSON
    web_index['shows'] = dict(web_index['shows'])
    
    # Save web index
    index_path = output_dir / 'index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(web_index, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"{'='*50}")
    print(f"Total characters processed: {char_count}")
    print(f"Characters skipped: {skipped_count}")
    print(f"Duplicate names handled: {duplicate_count}")
    print(f"Total shows: {len(web_index['shows'])}")
    print(f"Files created in: {output_dir}")
    
    # Verify
    actual_files = len(list(chars_dir.glob('*.json')))
    index_count = len(web_index['characters'])
    print(f"\nVerification:")
    print(f"  Character files created: {actual_files}")
    print(f"  Characters in index: {index_count}")
    if actual_files == index_count:
        print(f"  ✓ Counts match!")
    else:
        print(f"  ✗ WARNING: Counts don't match!")

if __name__ == '__main__':
    process_characters()