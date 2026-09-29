import json
import re
from pathlib import Path
from collections import defaultdict

SKIP_NAMES = {
    "open/close all folders",
    "general",
    "tropes",
    "characters",
    "spoiler",
    "ymmv",
}


def create_safe_filename(name):
    """Create a safe lowercase filename fragment from a character name."""
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    safe_name = re.sub(r"_+", "_", safe_name)
    return safe_name.strip("_")[:50].lower()


def load_show_characters(raw_dir):
    """Load every character from the TV Tropes crawl, including repeat names."""
    records = []
    for path in sorted(raw_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: skipping unreadable file {path.name}")
            continue

        show_name = data.get("media_title") or path.stem
        show_id = path.stem
        for character in data.get("characters") or []:
            name = (character.get("name") or "").strip()
            if (
                not name
                or len(name) > 80
                or name.lower() in SKIP_NAMES
                or name.lower().startswith("characters")
                or re.search(r"\b(in general|as a whole|as a group|main characters)\b", name, re.I)
                or re.search(r"tropes\s+[a-z]\s*(?:to|-)\s*[a-z]", name, re.I)
                or re.fullmatch(r"[A-Z](?:\s*[-–—]\s*[A-Z])?", name)
            ):
                continue
            tropes = list(dict.fromkeys(character.get("tropes") or []))
            records.append({
                "name": name,
                "show": show_name,
                "show_id": show_id,
                "tropes": tropes,
            })
    return records


def assign_ids(records):
    """Give every character a unique file id, even when names collide."""
    used = set()
    for record in records:
        safe_name = create_safe_filename(record["name"]) or "character"
        char_id = f"{record['show_id']}_{safe_name}"
        if char_id in used:
            suffix = 2
            while f"{char_id}_{suffix}" in used:
                suffix += 1
            char_id = f"{char_id}_{suffix}"
        used.add(char_id)
        record["id"] = char_id


def precompute_similar(records, limit=8):
    """Rank neighbors from trait vectors, then trope overlap when a vector is too thin."""
    from trait_layer import attach_trait_similarity

    stats = attach_trait_similarity(records, limit=limit)
    missing = [
        index for index, record in enumerate(records)
        if not record["similar"] and len(record.get("tropes") or []) >= 2
    ]
    print(f"Trait similarity left {len(missing)} characters; scoring those from tropes", flush=True)
    if missing:
        _trope_similar_for(records, set(missing), limit)
    return stats


def _trope_similar_for(records, needed, limit=8):
    """Jaccard fallback for characters whose tropes never became traits."""
    inverted = defaultdict(list)
    for index, record in enumerate(records):
        record["trope_set"] = set(record["tropes"])
        for trope in record["trope_set"]:
            inverted[trope].append(index)

    # Very common tropes create huge candidate lists and weak matches.
    useful = {trope: indexes for trope, indexes in inverted.items() if 1 < len(indexes) <= 1000}
    print(f"Using {len(useful)} distinctive tropes for similarity", flush=True)

    for index in needed:
        record = records[index]
        if len(record["trope_set"]) < 2:
            continue
        shared_counts = defaultdict(int)
        for trope in record["trope_set"]:
            for other_index in useful.get(trope, ()):
                if other_index != index:
                    shared_counts[other_index] += 1
        if len(shared_counts) > 800:
            shared_counts = dict(sorted(shared_counts.items(), key=lambda item: -item[1])[:800])

        target = record["trope_set"]
        ranked = []
        for other_index, shared in shared_counts.items():
            if shared < 2:
                continue
            other = records[other_index]
            shared_all = len(target & other["trope_set"])
            union = len(target | other["trope_set"])
            similarity = shared_all / union if union else 0
            if shared_all < 4 or similarity < 0.035:
                continue
            ranked.append({
                "name": other["name"],
                "show": other["show"],
                "id": other["id"],
                "similarity": round(similarity, 4),
                "shared_tropes": shared_all,
            })
        ranked.sort(key=lambda item: (-item["similarity"], -item["shared_tropes"], item["name"]))
        record["similar"] = ranked[:limit]
        if index and index % 2000 == 0:
            print(f"Scored similarity for {index} characters...", flush=True)


def process_characters():
    """Write the web index and one JSON file per character."""
    raw_dir = Path(__file__).resolve().parent.parent / "data" / "raw" / "tvtropes"
    output_dir = Path(__file__).resolve().parent.parent / "docs" / "web" / "web_data"
    chars_dir = output_dir / "characters"
    output_dir.mkdir(parents=True, exist_ok=True)
    chars_dir.mkdir(exist_ok=True)

    print(f"Reading shows from {raw_dir}")
    records = load_show_characters(raw_dir)
    assign_ids(records)
    print(f"Loaded {len(records)} characters from {len(list(raw_dir.glob('*.json')))} shows")
    precompute_similar(records)

    for old_file in chars_dir.glob("*.json"):
        old_file.unlink()
    print("Cleared old character files")

    web_index = {"characters": [], "shows": defaultdict(list)}
    for record in records:
        char_file = {
            "name": record["name"],
            "show": record["show"],
            "trope_count": len(record["tropes"]),
            "tropes": record["tropes"],
            "tropes_by_category": {},
            "traits": record.get("traits") or [],
            "similar": record["similar"],
        }
        with open(chars_dir / f"{record['id']}.json", "w", encoding="utf-8") as handle:
            json.dump(char_file, handle, ensure_ascii=False)

        summary = {
            "name": record["name"],
            "show": record["show"],
            "trope_count": len(record["tropes"]),
            "id": record["id"],
        }
        web_index["characters"].append(summary)
        web_index["shows"][record["show"]].append(summary)

    web_index["shows"] = dict(web_index["shows"])
    with open(output_dir / "index.json", "w", encoding="utf-8") as handle:
        json.dump(web_index, handle, ensure_ascii=False)

    print(f"Characters: {len(records)}")
    print(f"Shows: {len(web_index['shows'])}")
    print(f"Wrote {output_dir}")


if __name__ == "__main__":
    process_characters()
