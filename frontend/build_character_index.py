# build_character_index.py
"""
Script to build a master index of all characters from TV Tropes JSON files.
Run this once (or whenever data updates) to generate the character index.
"""

import os
import json
import pandas as pd
from collections import defaultdict

def build_character_index(data_dir="../data/raw/tvtropes", output_file="character_index.json"):
    """
    Scans all JSON files in the TV Tropes data directory and builds
    a master index of character names -> list of (media_title, file) locations.
    Also builds a media index for searching by show.
    """
    
    print(f"🔍 Scanning for character data in: {data_dir}")
    
    # Structure: { "character_name": [ {"media_title": ..., "source_file": ...}, ... ] }
    character_index = defaultdict(list)
    
    # Structure: { "media_title": [ {"name": ..., "source_file": ..., "trope_count": ...}, ... ] }
    media_index = defaultdict(list)
    
    # Also build a searchable lowercase -> original name mapping
    name_lookup = {}  # lowercase_name -> set of original names
    media_lookup = {}  # lowercase_media -> set of original media titles
    
    files_processed = 0
    characters_found = 0
    
    json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
    total_files = len(json_files)
    
    print(f"Found {total_files} JSON files to process\n")
    
    for i, filename in enumerate(json_files, 1):
        filepath = os.path.join(data_dir, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                df = pd.read_json(f)
                
            if "characters" not in df.columns:
                continue
                
            chars = df["characters"]
            for char in chars:
                name = char.get("name", "")
                media_title = char.get("media_title", "Unknown")
                trope_count = len(char.get("tropes", []))
                
                # Skip folder markers and empty names
                if not name or name == "open/close all folders":
                    continue
                
                # Add to character index
                character_index[name].append({
                    "media_title": media_title,
                    "source_file": filename,
                    "trope_count": trope_count
                })
                
                # Add to media index
                media_index[media_title].append({
                    "name": name,
                    "source_file": filename,
                    "trope_count": trope_count
                })
                
                # Add to character name lookup (for fuzzy/partial matching)
                name_lower = name.lower()
                if name_lower not in name_lookup:
                    name_lookup[name_lower] = set()
                name_lookup[name_lower].add(name)
                
                # Add to media lookup (for fuzzy/partial matching)
                media_lower = media_title.lower()
                if media_lower not in media_lookup:
                    media_lookup[media_lower] = set()
                media_lookup[media_lower].add(media_title)
                
                characters_found += 1
                
            files_processed += 1
            
            # Progress indicator
            if i % 50 == 0 or i == total_files:
                print(f"  Progress: {i}/{total_files} files ({characters_found:,} characters found)")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Convert sets to lists for JSON serialization
    name_lookup_serializable = {k: list(v) for k, v in name_lookup.items()}
    media_lookup_serializable = {k: list(v) for k, v in media_lookup.items()}
    
    # Build final output
    output = {
        "metadata": {
            "files_processed": files_processed,
            "total_characters": characters_found,
            "unique_names": len(character_index),
            "unique_media": len(media_index)
        },
        "characters": dict(character_index),
        "media": dict(media_index),
        "name_lookup": name_lookup_serializable,
        "media_lookup": media_lookup_serializable
    }
    
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nIndex built successfully!")
    print(f"   Files processed: {files_processed}")
    print(f"   Total character entries: {characters_found:,}")
    print(f"    Unique character names: {len(character_index):,}")
    print(f"   Unique media titles: {len(media_index):,}")
    print(f"   Saved to: {output_file}")
    
    return output


if __name__ == "__main__":
    build_character_index()