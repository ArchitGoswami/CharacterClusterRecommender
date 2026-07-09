import json
import os
from pathlib import Path
from collections import defaultdict

def prepare_web_data():
    """
    Prepares data for the web interface
    """
    
    # Load the existing character index
    print("Loading character index...")
    with open('character_index.json', 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # Create output directory
    web_data_dir = Path('web_data')
    web_data_dir.mkdir(exist_ok=True)
    
    characters_dir = web_data_dir / 'characters'
    characters_dir.mkdir(exist_ok=True)
    
    # Prepare simplified index
    simplified_index = {
        'characters': {},
        'shows': {}
    }
    
    # Load raw data directory
    raw_data_dir = Path('../data/raw/tvtropes')
    
    characters_dict = index_data['characters']
    
    print(f"Processing characters...")
    print(f"Total entries: {len(characters_dict)}")
    
    character_count = 0
    error_count = 0
    skipped_count = 0
    
    for char_name, char_info_list in characters_dict.items():
        try:
            # Handle list structure - take the first entry
            if isinstance(char_info_list, list):
                if len(char_info_list) == 0:
                    skipped_count += 1
                    continue
                char_info = char_info_list[0]  # Take first occurrence
            elif isinstance(char_info_list, dict):
                char_info = char_info_list
            else:
                skipped_count += 1
                continue
            
            # Extract fields
            media_title = char_info.get('media_title', 'Unknown Show')
            trope_count = char_info.get('trope_count', 0)
            source_file = char_info.get('source_file', '')
            
            if not source_file:
                skipped_count += 1
                continue
            
            # Create character ID
            char_id = source_file.replace('.json', '').replace('/', '_').replace('\\', '_')
            
            # Add to simplified index
            simplified_index['characters'][char_name] = {
                'show': media_title,
                'trope_count': trope_count,
                'id': char_id
            }
            
            # Group by show
            if media_title not in simplified_index['shows']:
                simplified_index['shows'][media_title] = []
            
            simplified_index['shows'][media_title].append({
                'name': char_name,
                'trope_count': trope_count,
                'id': char_id
            })
            
            # Load and process full character data
            source_file_path = raw_data_dir / source_file
            if source_file_path.exists():
                with open(source_file_path, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                
                # Process character data
                char_data = process_character_data(char_name, full_data, char_info)
                
                # Save individual character file
                safe_char_name = char_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                safe_char_name = "".join(c for c in safe_char_name if c.isalnum() or c == "_")[:50]
                output_file = characters_dir / f'{char_id}_{safe_char_name}.json'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(char_data, f, indent=2, ensure_ascii=False)
                
                character_count += 1
                
                if character_count % 100 == 0:
                    print(f"  ✓ Processed {character_count} characters...")
            else:
                error_count += 1
                if error_count <= 5:
                    print(f"  File not found: {source_file_path}")
            
        except Exception as e:
            error_count += 1
            if error_count <= 10:
                print(f"  Error processing {char_name}: {e}")
            continue
    
    # Save simplified index
    print("\nSaving index...")
    with open(web_data_dir / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_index, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully processed: {character_count} characters")
    print(f"✓ Shows indexed: {len(simplified_index['shows'])}")
    print(f"⚠ Skipped entries: {skipped_count}")
    print(f"✗ Errors: {error_count}")
    print(f"✓ Data saved to: {web_data_dir}/")
    print(f"{'='*60}\n")
    
    # Show some stats
    if character_count > 0:
        avg_tropes = sum(c['trope_count'] for c in simplified_index['characters'].values()) / len(simplified_index['characters'])
        print(f"Average tropes per character: {avg_tropes:.1f}")
        
        # Top shows by character count
        top_shows = sorted(
            simplified_index['shows'].items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        )[:10]
        
        print(f"\nTop 10 shows by character count:")
        for show, chars in top_shows:
            print(f"  • {show}: {len(chars)} characters")
    
    return simplified_index

def process_character_data(char_name, full_data, char_info):
    """Process and structure character data for the web interface"""
    
    tropes_by_category = defaultdict(list)
    all_tropes = []
    
    # Find character data
    character_data = None
    
    if 'characters' in full_data and isinstance(full_data['characters'], dict):
        characters_section = full_data['characters']
        
        # Try exact match
        if char_name in characters_section:
            character_data = characters_section[char_name]
        else:
            # Try case-insensitive
            char_name_lower = char_name.lower()
            for key, value in characters_section.items():
                if key.lower() == char_name_lower:
                    character_data = value
                    break
    
    # Extract tropes
    if character_data and isinstance(character_data, dict):
        tropes_data = character_data.get('tropes', [])
        
        if isinstance(tropes_data, list):
            for item in tropes_data:
                if isinstance(item, dict):
                    trope_name = item.get('name', item.get('trope', 'Unknown'))
                    trope_category = item.get('category', 'Uncategorized')
                elif isinstance(item, str):
                    trope_name = item
                    trope_category = 'Uncategorized'
                else:
                    continue
                
                all_tropes.append(trope_name)
                tropes_by_category[trope_category].append(trope_name)
        
        elif isinstance(tropes_data, dict):
            # Tropes organized by category
            for category, tropes_list in tropes_data.items():
                if isinstance(tropes_list, list):
                    for trope in tropes_list:
                        trope_name = trope if isinstance(trope, str) else str(trope)
                        all_tropes.append(trope_name)
                        tropes_by_category[category].append(trope_name)
    
    # Remove duplicates while preserving order
    all_tropes = list(dict.fromkeys(all_tropes))
    tropes_by_category = {
        cat: list(dict.fromkeys(tropes)) 
        for cat, tropes in tropes_by_category.items()
    }
    
    return {
        'name': char_name,
        'show': char_info.get('media_title', 'Unknown Show'),
        'trope_count': len(all_tropes),
        'tropes': all_tropes,
        'tropes_by_category': tropes_by_category
    }

if __name__ == '__main__':
    prepare_web_data()