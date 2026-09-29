"""Map TV Tropes names onto the 638-trait list, then score characters in that space.

The vector stays 638 dimensions long, one slot per trait in traits.py. A trope
word turns on one primary trait, not every near-synonym, so "evil" counts as
cruelty once. Traits that show up on too many characters are left out of the
similarity score. What remains is still the same list, just the part that
actually separates people.
"""

import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from traits import TRAIT_TO_INDEX

SPLIT_TROPE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+")
NEGATORS = {"not", "non", "anti", "faux", "fake"}
FILLERS = {"so", "very", "much", "even", "really", "a", "the"}

# Trope jargon that does not share a spelling with the trait it implies.
# Values are (trait, weight). Trait names must exist in traits.py.
TOKEN_TRAITS = {
    "snarker": [("sarcastic", 1.0)],
    "snark": [("sarcastic", 1.0)],
    "sassy": [("sarcastic", 0.7)],
    "deadpan": [("impassive", 1.0)],
    "dry": [("dry", 0.8)],
    "evil": [("cruel", 0.7)],
    "villain": [("amoral", 0.45)],
    "villainous": [("cruel", 0.8)],
    "villainy": [("cruel", 0.55)],
    "hero": [("heroic", 1.0)],
    "heroes": [("heroic", 1.0)],
    "heroic": [("heroic", 1.0)],
    "badass": [("tough", 0.85), ("confident", 0.45)],
    "bruiser": [("tough", 0.55)],
    "nice": [("kind", 1.0)],
    "kindness": [("kind", 1.0)],
    "jerk": [("abrasive", 1.0)],
    "jerkass": [("abrasive", 1.0)],
    "asshole": [("abrasive", 1.0)],
    "bastard": [("abrasive", 0.8)],
    "bitch": [("abrasive", 0.75)],
    "mean": [("cruel", 0.7)],
    "abusive": [("cruel", 1.0)],
    "bully": [("cruel", 0.75)],
    "sadist": [("sadistic", 1.0)],
    "bloodthirsty": [("sadistic", 0.8)],
    "brutal": [("brutal", 1.0)],
    "brutality": [("brutal", 1.0)],
    "violent": [("brutal", 0.65)],
    "ruthless": [("callous", 0.85)],
    "merciless": [("callous", 0.8)],
    "heartless": [("callous", 0.9)],
    "sociopath": [("callous", 1.0)],
    "sociopathic": [("callous", 1.0)],
    "psychopath": [("callous", 0.9)],
    "psychopathic": [("callous", 0.9)],
    "psycho": [("crazy", 0.9)],
    "crazy": [("crazy", 1.0)],
    "insane": [("crazy", 1.0)],
    "cloudcuckoolander": [("crazy", 1.0)],
    "mad": [("crazy", 0.45)],
    "genius": [("intelligent", 1.0)],
    "smart": [("intelligent", 1.0)],
    "prodigy": [("intelligent", 0.8)],
    "cunning": [("shrewd", 1.0)],
    "dumb": [("stupid", 1.0)],
    "ditz": [("stupid", 0.9)],
    "idiot": [("stupid", 0.9)],
    "airhead": [("stupid", 0.6)],
    "oblivious": [("absentminded", 0.6)],
    "bookworm": [("studious", 0.8)],
    "scholar": [("scholarly", 0.8)],
    "wise": [("wise", 1.0)],
    "foolish": [("foolish", 1.0)],
    "incompetent": [("foolish", 0.5)],
    "berserk": [("angry", 1.0)],
    "temper": [("angry", 1.0)],
    "wrath": [("angry", 0.9)],
    "angry": [("angry", 1.0)],
    "affably": [("amiable", 1.0)],
    "amiable": [("amiable", 1.0)],
    "stoic": [("stoic", 1.0)],
    "smug": [("arrogant", 1.0)],
    "snob": [("arrogant", 0.75)],
    "elitist": [("arrogant", 0.7)],
    "boastful": [("arrogant", 0.65)],
    "braggart": [("arrogant", 0.7)],
    "vain": [("narcissistic", 0.75)],
    "narcissist": [("narcissistic", 1.0)],
    "ego": [("egocentric", 0.65)],
    "manipulative": [("scheming", 1.0)],
    "manipulator": [("scheming", 1.0)],
    "schemer": [("scheming", 1.0)],
    "scheming": [("scheming", 1.0)],
    "scheme": [("scheming", 0.7)],
    "gambit": [("scheming", 0.75)],
    "trickster": [("crafty", 1.0)],
    "sly": [("sly", 1.0)],
    "hypocrite": [("deceitful", 0.85), ("sanctimonious", 0.7)],
    "liar": [("deceitful", 1.0)],
    "lies": [("deceitful", 0.8)],
    "lying": [("deceitful", 0.9)],
    "cheat": [("deceitful", 0.7)],
    "thief": [("thievish", 0.8)],
    "traitor": [("treacherous", 1.0)],
    "betrayal": [("treacherous", 1.0)],
    "backstab": [("treacherous", 0.9)],
    "coward": [("cowardly", 1.0)],
    "brave": [("courageous", 1.0)],
    "bravery": [("courageous", 1.0)],
    "fearless": [("courageous", 0.8)],
    "fearful": [("fearful", 0.7)],
    "loyal": [("loyal", 1.0)],
    "loyalty": [("loyal", 1.0)],
    "faithful": [("faithful", 1.0)],
    "revenge": [("vindictive", 1.0)],
    "vengeance": [("vindictive", 1.0)],
    "vengeful": [("vindictive", 1.0)],
    "grudge": [("resentful", 0.8)],
    "forgive": [("forgiving", 0.8)],
    "merciful": [("forgiving", 0.8)],
    "sacrifice": [("selfless", 0.75)],
    "martyr": [("selfless", 0.8)],
    "selfish": [("selfish", 1.0)],
    "selfless": [("selfless", 1.0)],
    "greedy": [("greedy", 1.0)],
    "generous": [("generous", 1.0)],
    "miser": [("miserly", 0.8)],
    "jealous": [("envious", 1.0)],
    "envy": [("envious", 1.0)],
    "possessive": [("possessive", 0.8)],
    "obsessive": [("obsessive", 1.0)],
    "stalker": [("predatory", 0.85)],
    "yandere": [("obsessive", 0.9), ("cruel", 0.55)],
    "tsundere": [("abrasive", 0.6), ("romantic", 0.45)],
    "kuudere": [("impassive", 0.9)],
    "dandere": [("shy", 0.9)],
    "genki": [("energetic", 1.0)],
    "perky": [("cheerful", 0.85)],
    "cheerful": [("cheerful", 1.0)],
    "gloomy": [("gloomy", 1.0)],
    "brooding": [("melancholic", 0.85)],
    "angst": [("melancholic", 0.65)],
    "angsty": [("melancholic", 0.65)],
    "tragic": [("melancholic", 0.6)],
    "funny": [("humorous", 1.0)],
    "comic": [("humorous", 0.45)],
    "witty": [("witty", 1.0)],
    "silly": [("silly", 0.7)],
    "goofy": [("playful", 0.7)],
    "playful": [("playful", 1.0)],
    "childish": [("childish", 1.0)],
    "immature": [("childish", 0.8)],
    "mature": [("mature", 0.7)],
    "ham": [("dramatic", 1.0)],
    "hammy": [("dramatic", 1.0)],
    "dramatic": [("dramatic", 1.0)],
    "serious": [("serious", 0.7)],
    "calm": [("calm", 0.8)],
    "passionate": [("passionate", 0.8)],
    "apathetic": [("apathetic", 0.8)],
    "enthusiastic": [("enthusiastic", 0.8)],
    "curious": [("curious", 0.8)],
    "nosy": [("meddlesome", 0.7)],
    "gossip": [("meddlesome", 0.5)],
    "romantic": [("romantic", 1.0)],
    "romance": [("romantic", 0.35)],
    "flirt": [("romantic", 0.65)],
    "pervert": [("libidinous", 1.0)],
    "lecherous": [("libidinous", 0.9)],
    "innocent": [("naive", 0.65)],
    "naive": [("naive", 1.0)],
    "gullible": [("gullible", 1.0)],
    "corrupt": [("amoral", 0.75)],
    "amoral": [("amoral", 1.0)],
    "immoral": [("amoral", 0.8)],
    "noble": [("honorable", 0.7)],
    "honorable": [("honorable", 1.0)],
    "honest": [("honest", 1.0)],
    "dishonest": [("dishonest", 1.0)],
    "blunt": [("blunt", 0.7)],
    "rude": [("discourteous", 0.8)],
    "polite": [("courteous", 0.7)],
    "gentle": [("gentle", 0.8)],
    "kind": [("kind", 1.0)],
    "cruel": [("cruel", 1.0)],
    "sweet": [("sweet", 0.6)],
    "bitter": [("resentful", 0.55)],
    "friendly": [("friendly", 1.0)],
    "buds": [("friendly", 0.55)],
    "vitriolic": [("abrasive", 0.85)],
    "loner": [("solitary", 1.0)],
    "solitary": [("solitary", 0.8)],
    "misanthrope": [("asocial", 0.9)],
    "leader": [("leaderly", 0.8)],
    "mentor": [("teacherly", 0.75)],
    "tyrant": [("domineering", 0.85)],
    "dictator": [("authoritarian", 0.8)],
    "rebel": [("iconoclastic", 0.75)],
    "rebellious": [("iconoclastic", 0.75)],
    "anarchist": [("iconoclastic", 0.6)],
    "obedient": [("obedient", 0.6)],
    "stubborn": [("stubborn", 1.0)],
    "determined": [("determined", 1.0)],
    "determinator": [("determined", 1.0)],
    "lazy": [("lazy", 1.0)],
    "slacker": [("lazy", 0.8)],
    "workaholic": [("hardworking", 0.9)],
    "diligent": [("hardworking", 0.8)],
    "ambitious": [("ambitious", 1.0)],
    "patient": [("patient", 0.8)],
    "impatient": [("impatient", 0.8)],
    "impulsive": [("impulsive", 1.0)],
    "reckless": [("impulsive", 0.85)],
    "cautious": [("cautious", 0.7)],
    "paranoid": [("paranoid", 1.0)],
    "suspicious": [("suspicious", 0.7)],
    "distrust": [("suspicious", 0.7)],
    "trusting": [("trusting", 0.6)],
    "shy": [("shy", 1.0)],
    "timid": [("timid", 0.8)],
    "bold": [("daring", 0.6)],
    "confident": [("confident", 0.8)],
    "insecure": [("insecure", 0.8)],
    "optimistic": [("optimistic", 0.8)],
    "pessimist": [("cynical", 0.7)],
    "pessimistic": [("cynical", 0.75)],
    "cynic": [("cynical", 1.0)],
    "cynical": [("cynical", 1.0)],
    "idealist": [("idealistic", 1.0)],
    "idealistic": [("idealistic", 1.0)],
    "arrogant": [("arrogant", 1.0)],
    "humble": [("humble", 1.0)],
    "modest": [("modest", 0.7)],
    "proud": [("proud", 0.7)],
    "quiet": [("quiet", 0.45)],
    "loud": [("boisterous", 0.55)],
    "boisterous": [("boisterous", 0.7)],
    "outgoing": [("sociable", 0.7)],
    "sociable": [("sociable", 0.8)],
    "charming": [("charming", 0.8)],
    "charismatic": [("charismatic", 0.9)],
    "awkward": [("shy", 0.4)],
    "clumsy": [("clumsy", 0.6)],
    "klutz": [("clumsy", 0.7)],
    "competent": [("capable", 0.55)],
    "protective": [("protective", 0.8)],
    "overprotective": [("protective", 0.5), ("possessive", 0.45)],
    "caring": [("caring", 0.8)],
    "compassionate": [("compassionate", 0.9)],
    "empathy": [("empathetic", 0.8)],
    "empathetic": [("empathetic", 0.9)],
    "cold": [("cold", 0.65)],
    "warm": [("warm", 0.55)],
    "aloof": [("aloof", 0.8)],
    "creepy": [("disturbing", 0.85)],
    "disturbing": [("disturbing", 0.7)],
    "hate": [("hateful", 0.75)],
    "hateful": [("hateful", 0.9)],
    "tragic": [("melancholic", 0.55)],
    "repentant": [("repentant", 0.8)],
    "redeemed": [("repentant", 0.45)],
    "fanatic": [("fanatical", 0.9)],
    "zealot": [("fanatical", 0.85)],
    "extremist": [("fanatical", 0.6)],
    "pious": [("religious", 0.6)],
    "religious": [("religious", 0.55)],
    "atheist": [("irreligious", 0.5)],
    "skeptical": [("skeptical", 0.7)],
    "drunk": [("dissolute", 0.4)],
    "alcoholic": [("dissolute", 0.45)],
    "glutton": [("hedonistic", 0.45)],
    "sane": [("sane", 0.55)],
    "harmless": [("inoffensive", 0.7)],
    "helpful": [("helpful", 0.6)],
    "tough": [("tough", 0.7)],
    "weak": [("weak", 0.35)],
    "pure": [("pure", 0.4)],
    "manly": [("masculine", 0.45)],
    "adorkable": [("cute", 0.55)],
    "cute": [("cute", 0.4)],
    "cutie": [("cute", 0.35)],
    "controlfreak": [("domineering", 1.0)],
    "strongwilled": [("strong-willed", 1.0)],
}

# A negated trait lands here instead of the original. Missing entries are dropped.
CONTRARY = {
    "heroic": "cynical",
    "kind": "cruel",
    "honest": "deceitful",
    "loyal": "treacherous",
    "courageous": "cowardly",
    "sane": "crazy",
    "intelligent": "stupid",
    "amiable": "deceitful",
    "inoffensive": "cruel",
    "friendly": "aloof",
    "calm": "angry",
    "humble": "arrogant",
    "generous": "greedy",
    "cheerful": "gloomy",
    "trusting": "suspicious",
}

# Traits on more characters than this nominate too many neighbors.
# They still count once two characters are already paired by a rarer trait.
NOMINATOR_MAX_DF = 2500


def _check_lexicon():
    missing = set()
    for pairs in TOKEN_TRAITS.values():
        for trait, _weight in pairs:
            if trait not in TRAIT_TO_INDEX:
                missing.add(trait)
    for trait in CONTRARY.values():
        if trait not in TRAIT_TO_INDEX:
            missing.add(trait)
    if missing:
        raise RuntimeError(f"Lexicon uses unknown traits: {sorted(missing)}")


_check_lexicon()


def split_trope(trope):
    return [token.lower() for token in SPLIT_TROPE.findall(trope)]


def _lookup(token):
    # Only the explicit map. A trait word inside an unrelated trope
    # (CriminalMind, MistakenIdentity) is not evidence of that trait.
    return TOKEN_TRAITS.get(token, ())


def _add(weights, trait, weight):
    if not trait or weight <= 0:
        return
    weights[trait] = min(1.0, weights.get(trait, 0.0) + weight)


def traits_for_trope(trope):
    """Sparse trait weights for one trope name. Each trait is at most 1."""
    tokens = split_trope(trope)
    weights = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in NEGATORS and index + 1 < len(tokens):
            nxt = index + 1
            while nxt < len(tokens) and tokens[nxt] in FILLERS:
                nxt += 1
            if nxt < len(tokens):
                if token == "anti" and tokens[nxt] in {"hero", "heroes", "heroic"}:
                    _add(weights, "cynical", 0.85)
                    _add(weights, "heroic", 0.35)
                    index = nxt + 1
                    continue
                mapped = _lookup(tokens[nxt])
                if mapped:
                    for trait, weight in mapped:
                        _add(weights, CONTRARY.get(trait), weight)
                    index = nxt + 1
                    continue
        for trait, weight in _lookup(token):
            _add(weights, trait, weight)
        index += 1
    return weights


_TROPE_CACHE = {}


def cached_trope_traits(trope):
    found = _TROPE_CACHE.get(trope)
    if found is None:
        found = traits_for_trope(trope)
        _TROPE_CACHE[trope] = found
    return found


def character_trait_weights(tropes):
    """Sum trope weights into one sparse trait vector."""
    totals = defaultdict(float)
    for trope in tropes:
        if not isinstance(trope, str):
            continue
        for trait, weight in cached_trope_traits(trope).items():
            totals[trait] += weight
    return dict(totals)


def attach_trait_similarity(records, limit=8):
    """Fill record['traits'] and rank neighbors by cosine similarity of trait vectors.

    Characters with fewer than three traits keep an empty neighbor list. The
    caller can fall back to trope overlap for those.
    """
    raw_vectors = []
    doc_freq = defaultdict(int)
    usable = 0
    for record in records:
        weights = character_trait_weights(record["tropes"])
        record["trait_weights"] = weights
        raw_vectors.append(weights)
        if len(weights) >= 3:
            usable += 1
        for trait in weights:
            doc_freq[trait] += 1

    population = len(records)
    active = {
        trait: freq
        for trait, freq in doc_freq.items()
        if freq >= 3
    }
    common = sorted(doc_freq.items(), key=lambda item: -item[1])[:12]
    print("Most common traits:", ", ".join(f"{trait} {freq}" for trait, freq in common), flush=True)
    print(
        f"Trait vectors: {usable} characters with 3+ traits, "
        f"{len(doc_freq)} traits fired, {len(active)} used for similarity",
        flush=True,
    )

    idf = {
        trait: math.log((population + 1) / (freq + 1))
        for trait, freq in doc_freq.items()
    }
    nominators = {trait for trait, freq in active.items() if freq <= NOMINATOR_MAX_DF}
    print(f"Nominating neighbors with {len(nominators)} less common traits", flush=True)

    normalized = []
    common_parts = []
    postings = defaultdict(list)
    for index, weights in enumerate(raw_vectors):
        scored = []
        for trait, value in weights.items():
            if trait not in active:
                continue
            scored.append((trait, math.log1p(value) * idf[trait]))
        norm = math.sqrt(sum(value * value for _trait, value in scored))
        if norm == 0:
            normalized.append({})
            common_parts.append(())
            continue
        full = {trait: value / norm for trait, value in scored}
        normalized.append(full)
        common_parts.append(tuple(
            (trait, weight) for trait, weight in full.items() if trait not in nominators
        ))
        for trait, weight in full.items():
            if trait in nominators:
                postings[trait].append((index, weight))

    stamp = [0] * population
    score = [0.0] * population
    touched = []
    run = 1

    for index, vector in enumerate(normalized):
        record = records[index]
        record["traits"] = _top_traits(raw_vectors[index], idf)
        record["similar"] = []
        vector = normalized[index]
        if len(vector) < 3:
            continue

        touched.clear()
        run += 1
        if run == 2_000_000_000:
            stamp = [0] * population
            run = 1
        for trait, value in vector.items():
            if trait not in nominators:
                continue
            for other_index, other_value in postings[trait]:
                if other_index == index:
                    continue
                if stamp[other_index] != run:
                    stamp[other_index] = run
                    score[other_index] = 0.0
                    touched.append(other_index)
                score[other_index] += value * other_value

        if len(touched) > 300:
            touched.sort(key=lambda other: score[other], reverse=True)
            del touched[300:]

        ranked = []
        target_traits = raw_vectors[index]
        for other_index in touched:
            similarity = score[other_index]
            for trait, value in common_parts[index]:
                similarity += value * normalized[other_index].get(trait, 0.0)
            if similarity < 0.2:
                continue
            other = records[other_index]
            shared = _shared_trait_names(target_traits, other["trait_weights"], idf)
            if len(shared) < 2:
                continue
            ranked.append({
                "name": other["name"],
                "show": other["show"],
                "id": other["id"],
                "similarity": round(similarity, 4),
                "shared_traits": shared,
                "shared_tropes": 0,
            })
        ranked.sort(key=lambda item: (-item["similarity"], item["name"]))
        record["similar"] = ranked[:limit]
        if index and index % 2000 == 0:
            print(f"Scored trait similarity for {index} characters...", flush=True)

    for record in records:
        record.pop("trait_weights", None)
    return {
        "characters_with_traits": usable,
        "traits_fired": len(doc_freq),
        "traits_for_similarity": len(active),
    }


def _strength(value, trait, idf):
    return math.log1p(value) * idf.get(trait, 0.0)


def _top_traits(weights, idf, limit=8):
    ranked = sorted(
        ((trait, value) for trait, value in weights.items() if trait in idf),
        key=lambda item: -_strength(item[1], item[0], idf),
    )
    if not ranked:
        return []
    peak = _strength(ranked[0][1], ranked[0][0], idf) or 1.0
    traits = []
    for trait, value in ranked[:limit]:
        traits.append({
            "name": _label(trait),
            "score": round(_strength(value, trait, idf) / peak, 3),
        })
    return traits


def _shared_trait_names(left, right, idf, limit=4):
    shared = []
    for trait, value in left.items():
        other = right.get(trait)
        if other and trait in idf:
            shared.append((trait, _strength(value, trait, idf) * math.log1p(other)))
    shared.sort(key=lambda item: -item[1])
    return [_label(trait) for trait, _score in shared[:limit]]


def _label(trait):
    return trait[:1].upper() + trait[1:] if trait else trait
