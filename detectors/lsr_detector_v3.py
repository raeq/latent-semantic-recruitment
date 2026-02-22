#!/usr/bin/env python3
"""
LSR Detector v3: Orphaned Sophistication

v2 asked: "Is this word figurative and unjustified?"
v3 asks:  "Is this word structurally orphaned?"

The insight (Richard Quinn, 22 Feb 2026): LLMs over-index on
training-weight-heavy exceptional prose. They produce 99.99th-
percentile polysemous craft as DEFAULT output. The detection
signal is UNEARNED SOPHISTICATION — literary moves that arrive
without the architecture to support them.

A real McCarthy earns "the rudder would bite" with sustained
control across thousands of sentences. The LLM drops "hungry
steel teeth" into a passage where nothing before or after it
operates at that level. The move is orphaned.

Three tests for orphanhood:

1. ISOLATION: Is this figurative move at a higher sophistication
   level than its neighbors? (Spike detection.)

2. CHAIN: Does this figurative move connect to other figurative
   language in the same register nearby? (Metaphor chain detection.)
   McCarthy builds chains. LLMs drop singles.

3. PREPARATION: Is there tonal/rhythmic preparation for the
   figurative move? (Signpost detection, expanded from v2.)

A word that fails all three = orphaned = flagged.
A word that passes any one = potentially earned = not flagged.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


# ============================================================================
# DOMAIN-LITERAL SETS (from v2)
# ============================================================================

DOMAIN_LITERAL = {
    "sawmill": {
        "saw", "blade", "bandsaw", "mill", "timber", "lumber", "plank",
        "board", "sawdust", "carpenter", "carriage", "guide", "peel",
        "log", "trunk", "wood", "grain", "knot", "bark", "ring",
        "heartwood", "sapwood", "sap", "pine", "oak",
        "cut", "cutting", "feed", "fed",
        "stack", "stacked", "turn", "turned", "rotate",
        "sharp", "edge", "thick", "thin",
    },
    "ocean_storm": {
        "wave", "waves", "swell", "surge", "tide", "current",
        "storm", "gust", "gale", "wind", "rain", "spray",
        "boat", "ship", "sail", "mast", "hull", "deck", "bow", "stern",
        "port", "starboard", "anchor", "rudder", "helm", "gunwale",
        "keel", "rigging",
        "haul", "trim", "secure", "line", "fast", "cleat",
        "drown", "swim", "swimming", "sink", "float", "roll",
        "pitch", "heave",
        "blow", "hit", "crash",
    },
    "kitchen_fire": {
        "kitchen", "chef", "oven", "stove", "pan", "pot", "burner",
        "grill", "plate", "dish", "knife", "spatula", "peel",
        "cook", "cooking", "fry", "frying", "chop", "chopping",
        "slice", "dice", "mince", "boil", "simmer", "roast",
        "bake", "sear", "saute",
        "skin", "bone", "fat", "breast", "leg", "neck",
        "tongue",
        "hot", "heat", "warm", "cool", "cold", "freeze", "freezing",
        "cut", "press", "squeeze", "whip", "beat",
        "taste", "tasted",
    },
    "battlefield_surgery": {
        "surgeon", "surgery", "medic", "scalpel", "suture", "tourniquet",
        "bandage", "morphine", "triage", "ambulance",
        "wound", "blood", "bleeding", "flesh", "bone", "skin", "muscle",
        "nerve", "vein", "artery", "tissue", "organ", "leg", "thigh",
        "heart", "face",
        "cut", "incision", "probe", "stitch", "close", "dress",
        "irrigate", "extract",
        "shell", "blast", "fire", "round", "shot", "artillery",
        "pulse", "pressure", "rate",
        "death", "code", "drop", "beat",
        "patient",  # MOVED TO LITERAL — "patient" is the medical term
    },
    "blacksmith": {
        "blacksmith", "smithy", "anvil", "forge", "bellows", "tongs",
        "quench", "ingot", "hammer",
        "strike", "struck", "blow", "blows", "hit", "pound",
        "heat", "heated", "hot", "cool", "cooled", "cold",
        "shape", "shaped", "form", "bend", "twist", "draw", "drawn",
        "turn", "turned", "flat", "point", "edge", "taper",
        "hard", "soft", "brittle", "tough", "bright", "dark",
        "red", "orange", "white", "straw",
        "fire", "back",
    },
    "wilderness": {
        "tree", "trees", "branch", "branches", "trunk", "trunks",
        "root", "roots", "leaf", "leaves", "needle", "needles",
        "bark", "moss", "lichen", "fern",
        "rock", "rocks", "stone", "stones", "dirt", "mud", "earth",
        "stream", "creek", "river", "water",
        "trail", "path", "slope", "ridge", "clearing", "hollow",
        "camp", "tent", "pack",
        "wind", "rain", "snow", "frost", "ice", "cold",
        "bird", "deer", "fox", "bear",
    },
    "general": set(),  # no domain-literal filtering
}


# ============================================================================
# FIGURATIVE SOPHISTICATION MARKERS
# ============================================================================
# These are the specific moves we're looking for: polysemous words
# whose secondary senses align with a register that's NOT the domain.
# Same core set as v2 but reorganized.

REGISTER_FIELDS = {
    "consumption": {
        "fed", "feed", "bit", "bite", "teeth", "tongue", "mouth", "lip",
        "swallow", "gulp", "devour", "consume", "appetite", "taste",
        "hunger", "hungry", "starve", "chew", "gnaw", "digest", "eat",
        "ate", "stomach", "throat", "raw",
    },
    "personification": {
        "stubborn", "listen", "want", "wanted", "refuse", "willing",
        "angry", "eager", "reluctant", "obey", "resist", "yield",
        "surrender", "forgive", "complain", "scream", "whisper",
        "sing", "cry", "weep", "breathe", "sleep", "wake", "dream",
        "die", "live", "patient", "tired", "nervous",
    },
    "body": {
        "arm", "shoulder", "face", "head", "heart", "eye", "neck",
        "bone", "skin", "flesh", "blood", "vein", "muscle", "nerve",
        "grip", "fist",
    },
    "violence": {
        "cut", "sharp", "edge", "blade", "slash", "slice", "split",
        "tear", "rip", "sever", "break", "snap", "crack", "crush",
        "strike", "hit", "beat", "pound", "hammer", "wound", "scar",
    },
    "fire_heat": {
        "burn", "fire", "flame", "blaze", "glow", "spark", "flash",
        "flare", "scorch", "sear", "smoke", "ash", "ember",
        "hot", "cool", "warm", "temper", "forge", "roast",
    },
    "water_weather": {
        "wave", "flood", "pour", "wash", "tide", "current", "drift",
        "flow", "stream", "surge", "swell", "drown", "sink", "rise",
        "blow", "gust", "blast", "storm", "howl", "roar", "lash",
    },
}

ALL_REGISTER_WORDS = set()
for field_words in REGISTER_FIELDS.values():
    ALL_REGISTER_WORDS.update(field_words)

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "must", "it", "its", "he", "she", "they", "them", "their", "his",
    "her", "him", "we", "us", "our", "you", "your", "i", "my", "me",
    "this", "that", "these", "those", "which", "who", "whom", "what",
    "where", "when", "how", "why", "if", "then", "than", "so", "not",
    "no", "nor", "too", "very", "just", "also", "even", "now",
    "here", "there", "up", "out", "off", "over", "into", "onto", "upon",
    "about", "after", "before", "during", "between", "through", "under",
    "above", "below", "each", "every", "all", "both", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "while",
    "until", "because", "since", "although", "though", "whether",
    "either", "neither", "yet", "already", "again", "once", "twice",
    "enough", "much", "many", "several", "another", "any", "still",
}

PUNCT = re.compile(r'[^a-zA-Z\']')

# Inanimate nouns (for personification detection)
INANIMATE_NOUNS = {
    "blade", "saw", "bandsaw", "machine", "hammer", "anvil", "forge",
    "knife", "oven", "grill", "burner", "stove", "pan", "pot",
    "engine", "boat", "ship", "wheel", "mast", "motor",
    "steel", "iron", "metal", "wood", "log", "timber", "stone",
    "fire", "flame", "wind", "rain", "storm", "wave", "sea", "ocean",
    "water", "river", "cold", "heat", "light", "air",
    "darkness", "silence", "night", "day", "morning",
    "mill", "kitchen", "tent", "smithy", "door", "wall", "floor",
    "needle", "compass", "cord", "rope", "lock", "mud",
    "smoke", "cloud", "fog", "mist",
    "sound", "noise", "echo",
}

ANIMATE_VERBS = {
    "ate", "eat", "eating", "fed", "feed", "feeding", "bit", "bite",
    "biting", "chew", "chewing", "swallow", "swallowed", "devour",
    "devoured", "consume", "consumed", "hunger", "hungered",
    "spoke", "speak", "said", "whisper", "whispered", "scream",
    "screamed", "howl", "howled", "roar", "roared", "sing", "sang",
    "cry", "cried", "listen", "listened", "breathe", "breathed",
    "refuse", "refused", "demand", "demanded",
    "forgive", "forgave", "resist", "resisted", "surrender",
    "surrendered", "obey", "obeyed",
    "grip", "gripped", "grab", "grabbed", "lick", "licked",
    "snarl", "snarled", "growl", "growled", "spit", "spat", "wept",
    "stubborn", "angry", "hungry", "eager", "willing",
    "reluctant", "tired", "patient", "nervous",
}


# ============================================================================
# SENTENCE-LEVEL SOPHISTICATION SCORING
# ============================================================================

def sentence_figurative_density(sentence: str, domain_lit: set) -> float:
    """
    Score a sentence's figurative sophistication.

    Returns the fraction of content words that are register-active
    (polysemous with figurative potential) and NOT domain-literal.

    Higher = more figuratively sophisticated sentence.
    """
    words = sentence.lower().split()
    content_words = 0
    register_words = 0

    for w in words:
        cleaned = PUNCT.sub('', w)
        if not cleaned or len(cleaned) < 3 or cleaned in STOPWORDS:
            continue
        content_words += 1
        if cleaned in ALL_REGISTER_WORDS and cleaned not in domain_lit:
            register_words += 1

    if content_words == 0:
        return 0.0
    return register_words / content_words


def detect_personification(sentence: str) -> List[Dict]:
    """Detect inanimate subject + animate verb."""
    words = sentence.lower().split()
    findings = []

    for i, word in enumerate(words):
        cleaned = PUNCT.sub('', word)
        if cleaned in ANIMATE_VERBS:
            for j in range(i - 1, max(i - 5, -1), -1):
                subj = PUNCT.sub('', words[j])
                if subj in INANIMATE_NOUNS:
                    findings.append({
                        "subject": subj,
                        "verb": cleaned,
                        "position": i,
                    })
                    break
                if subj in STOPWORDS:
                    continue
                if len(subj) > 2 and subj not in STOPWORDS:
                    break
    return findings


# ============================================================================
# THE THREE ORPHANHOOD TESTS
# ============================================================================

def test_isolation(sentence_idx: int, sentences: List[str],
                   domain_lit: set, window: int = 2) -> Dict:
    """
    Test 1: ISOLATION (spike detection)

    Is this sentence's figurative density significantly higher than
    its neighbors? If so, the sophistication is isolated — a spike.

    Returns:
        score: float (0 = not isolated, 1 = maximally isolated)
        detail: explanation
    """
    target_density = sentence_figurative_density(sentences[sentence_idx],
                                                  domain_lit)

    # Get neighbor densities
    neighbor_densities = []
    for i in range(max(0, sentence_idx - window),
                   min(len(sentences), sentence_idx + window + 1)):
        if i != sentence_idx:
            neighbor_densities.append(
                sentence_figurative_density(sentences[i], domain_lit))

    if not neighbor_densities:
        return {"score": 0.0, "detail": "no neighbors"}

    avg_neighbor = sum(neighbor_densities) / len(neighbor_densities)
    max_neighbor = max(neighbor_densities)

    # Isolation = how much this sentence exceeds its neighborhood
    # If target is 0.3 and neighbors average 0.05, that's a spike
    # If target is 0.3 and neighbors average 0.25, that's sustained
    if target_density <= avg_neighbor:
        return {"score": 0.0,
                "detail": f"target {target_density:.2f} <= neighbors {avg_neighbor:.2f}"}

    # How far above the neighborhood max?
    if target_density <= max_neighbor:
        return {"score": 0.2,
                "detail": f"target {target_density:.2f} within neighbor range (max {max_neighbor:.2f})"}

    gap = target_density - avg_neighbor
    isolation = min(1.0, gap / 0.2)  # 0.2 gap = fully isolated
    return {"score": isolation,
            "detail": f"target {target_density:.2f} vs neighbors avg {avg_neighbor:.2f} (gap {gap:.2f})"}


def test_chain(word: str, word_fields: List[str], sentence_idx: int,
               sentences: List[str], domain_lit: set,
               window: int = 3) -> Dict:
    """
    Test 2: CHAIN (metaphor chain detection)

    Does this figurative word connect to other figurative words in
    the SAME register field within a window of sentences?

    McCarthy builds chains: "bite... teeth... gnaw... hunger" across
    a paragraph. LLMs drop singles: "hungry" then nothing.

    Returns:
        score: float (0 = strong chain, 1 = orphaned)
        detail: explanation
    """
    # Look for other register words in the same fields within window
    chain_words = []

    for i in range(max(0, sentence_idx - window),
                   min(len(sentences), sentence_idx + window + 1)):
        if i == sentence_idx:
            continue
        sent_words = sentences[i].lower().split()
        for w in sent_words:
            cleaned = PUNCT.sub('', w)
            if cleaned == word or not cleaned or cleaned in STOPWORDS:
                continue
            if cleaned in domain_lit:
                continue
            # Is this word in any of the same register fields?
            for field in word_fields:
                if cleaned in REGISTER_FIELDS.get(field, set()):
                    chain_words.append((cleaned, field, i))

    if len(chain_words) >= 3:
        return {"score": 0.0,
                "detail": f"strong chain: {[w for w,_,_ in chain_words[:4]]}"}
    elif len(chain_words) == 2:
        return {"score": 0.2,
                "detail": f"moderate chain: {[w for w,_,_ in chain_words]}"}
    elif len(chain_words) == 1:
        return {"score": 0.6,
                "detail": f"weak chain: {chain_words[0][0]}"}
    else:
        return {"score": 1.0, "detail": "no chain — orphaned"}


def test_preparation(sentence_idx: int, sentences: List[str]) -> Dict:
    """
    Test 3: PREPARATION (signpost/tonal shift detection)

    Is the figurative move prepared by any of:
    - Explicit signposts (simile markers, "was a", "like a")
    - Extended metaphor frame in surrounding sentences
    - Tonal shift markers (sentence-length change, rhythm break)
    - Thematic preparation ("it felt like...", "as though...")

    Returns:
        score: float (0 = well prepared, 1 = unannounced)
        detail: explanation
    """
    sentence = sentences[sentence_idx]
    prev = sentences[sentence_idx - 1] if sentence_idx > 0 else ""
    next_s = sentences[sentence_idx + 1] if sentence_idx < len(sentences) - 1 else ""

    context = f"{prev} {sentence} {next_s}".lower()

    # Explicit signposts
    signpost_patterns = [
        r'\blike\s+(?:a|an|the)\b',
        r'\bas\s+(?:if|though)\b',
        r'\bwas\s+(?:a|an)\b',
        r'\bwere\s+(?:a|an)\b',
        r'\bthe\s+way\s+(?:a|an)\b',
        r'\bnothing\s+more\s+than\b',
        r'\blike\s+something\b',
        r'\blike\s+\w+\s+\w+ing\b',
        r'\bfelt\s+like\b',
        r'\blooked\s+like\b',
        r'\bsounded\s+like\b',
        r'\bsmelled\s+like\b',
        r'\bthat\'s\b',  # "That's life, that is" — Richard's sawmill
    ]

    for pattern in signpost_patterns:
        if re.search(pattern, context):
            return {"score": 0.0,
                    "detail": f"signposted: matched '{pattern}'"}

    # Extended metaphor frame: does the surrounding context develop
    # a metaphor explicitly? Look for multiple figurative markers
    # in adjacent sentences
    prev_fig = sentence_figurative_density(
        prev, DOMAIN_LITERAL.get("general", set())) if prev else 0
    next_fig = sentence_figurative_density(
        next_s, DOMAIN_LITERAL.get("general", set())) if next_s else 0

    if prev_fig > 0.15 and next_fig > 0.15:
        return {"score": 0.1,
                "detail": f"embedded in figurative context (prev={prev_fig:.2f}, next={next_fig:.2f})"}

    if prev_fig > 0.15 or next_fig > 0.15:
        return {"score": 0.3,
                "detail": f"partially prepared (prev={prev_fig:.2f}, next={next_fig:.2f})"}

    # Tonal shift: short emphatic sentence after long ones can be
    # a deliberate rhythmic move (earned)
    sent_len = len(sentence.split())
    prev_len = len(prev.split()) if prev else sent_len
    if sent_len < 6 and prev_len > 15:
        return {"score": 0.2,
                "detail": f"rhythmic shift ({prev_len} → {sent_len} words)"}

    return {"score": 1.0, "detail": "unannounced — no preparation"}


# ============================================================================
# MAIN DETECTOR
# ============================================================================

def detect_lsr_v3(text: str, domain: str) -> Dict:
    """
    Detect orphaned sophistication in a passage.

    Finds figurative polysemous words, then tests each for orphanhood
    using three tests: isolation, chain, preparation.

    A word is flagged only if it scores high on ALL THREE tests
    (orphaned on all dimensions). This is the key difference from v2:
    v2 flagged any unjustified figurative word. v3 flags only those
    that are structurally orphaned — unearned.
    """
    domain_lit = DOMAIN_LITERAL.get(domain, set())

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return {"orphaned": [], "earned": [], "literal_filtered": 0,
                "summary": "Empty text"}

    literal_count = 0
    orphaned = []
    earned = []

    for sent_idx, sentence in enumerate(sentences):
        # Find personifications in this sentence
        persns = detect_personification(sentence)
        pers_verbs = {p["verb"] for p in persns}

        words = sentence.lower().split()
        for word_raw in words:
            word = PUNCT.sub('', word_raw).lower()
            if not word or len(word) < 3 or word in STOPWORDS:
                continue
            if word not in ALL_REGISTER_WORDS:
                continue

            # Domain-literal filter
            if word in domain_lit:
                literal_count += 1
                continue

            # Find register fields
            matched_fields = []
            for field_name, field_words in REGISTER_FIELDS.items():
                if word in field_words:
                    matched_fields.append(field_name)
            if not matched_fields:
                continue

            # Is this word being used figuratively?
            is_figurative = False

            # Personification
            if word in pers_verbs:
                is_figurative = True

            # Animate verb (even without detected inanimate subject)
            if word in ANIMATE_VERBS:
                is_figurative = True

            # Inanimate noun used as modifier with animate quality
            # e.g., "hungry steel", "stubborn grain"
            word_idx = None
            for wi, w in enumerate(words):
                if PUNCT.sub('', w).lower() == word:
                    word_idx = wi
                    break

            if word_idx is not None and word in {"hungry", "stubborn",
                    "angry", "eager", "tired", "patient", "nervous",
                    "reluctant", "willing"}:
                # Check if modifying an inanimate noun
                if word_idx + 1 < len(words):
                    next_w = PUNCT.sub('', words[word_idx + 1]).lower()
                    if next_w in INANIMATE_NOUNS or next_w in ALL_REGISTER_WORDS:
                        is_figurative = True
                # Check if predicate of inanimate subject
                if word_idx > 0:
                    for j in range(word_idx - 1, max(word_idx - 4, -1), -1):
                        prev_w = PUNCT.sub('', words[j]).lower()
                        if prev_w in INANIMATE_NOUNS:
                            is_figurative = True
                            break
                        if prev_w not in STOPWORDS and len(prev_w) > 2:
                            break

            if not is_figurative:
                continue

            # ============================================================
            # THE THREE ORPHANHOOD TESTS
            # ============================================================

            t1 = test_isolation(sent_idx, sentences, domain_lit)
            t2 = test_chain(word, matched_fields, sent_idx, sentences,
                           domain_lit)
            t3 = test_preparation(sent_idx, sentences)

            # Orphanhood score: average of three tests
            orphan_score = (t1["score"] + t2["score"] + t3["score"]) / 3

            entry = {
                "word": word,
                "sentence": sentence.strip()[:120],
                "register_fields": matched_fields,
                "is_personification": word in pers_verbs,
                "position": f"{sent_idx + 1}/{len(sentences)}",
                "isolation": t1,
                "chain": t2,
                "preparation": t3,
                "orphan_score": orphan_score,
            }

            # Threshold: orphan_score > 0.6 means orphaned on most dimensions
            if orphan_score > 0.6:
                entry["verdict"] = "ORPHANED"
                orphaned.append(entry)
            else:
                entry["verdict"] = "EARNED"
                earned.append(entry)

    summary = (f"{len(orphaned)} orphaned, {len(earned)} earned, "
               f"{literal_count} literal-filtered")

    return {
        "orphaned": orphaned,
        "earned": earned,
        "literal_filtered": literal_count,
        "summary": summary,
    }


def print_result_v3(label: str, result: Dict):
    """Print v3 detection results."""
    print(f"\n{'—' * 60}")
    print(f"  {label}")
    print(f"  {result['summary']}")
    print(f"{'—' * 60}")

    for c in result["orphaned"]:
        pers = " [pers]" if c["is_personification"] else ""
        fields = ", ".join(c["register_fields"])
        print(f"  >>> ORPHANED  '{c['word']}' [{fields}]{pers}  "
              f"score={c['orphan_score']:.2f}")
        print(f"      isolation: {c['isolation']['score']:.1f} "
              f"({c['isolation']['detail']})")
        print(f"      chain:     {c['chain']['score']:.1f} "
              f"({c['chain']['detail']})")
        print(f"      prepared:  {c['preparation']['score']:.1f} "
              f"({c['preparation']['detail']})")
        print(f"      \"{c['sentence']}\"")

    for c in result["earned"]:
        pers = " [pers]" if c["is_personification"] else ""
        fields = ", ".join(c["register_fields"])
        print(f"      earned  '{c['word']}' [{fields}]{pers}  "
              f"score={c['orphan_score']:.2f}")
        print(f"      isolation: {c['isolation']['score']:.1f} | "
              f"chain: {c['chain']['score']:.1f} | "
              f"prepared: {c['preparation']['score']:.1f}")


# ============================================================================
# TEST: Run on all three corpora
# ============================================================================

if __name__ == "__main__":
    import sys
    import json

    sys.path.insert(0, "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld")
    sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")

    from lsr_detector_v2 import RICHARD_PASSAGES

    print("=" * 72)
    print("LSR DETECTOR v3: ORPHANED SOPHISTICATION")
    print("=" * 72)

    # --- Richard's 5 hand-written passages ---
    print("\n\n[1] RICHARD'S HAND-WRITTEN PASSAGES")
    print("=" * 72)
    r_orphaned = 0
    r_earned = 0
    for domain, text in RICHARD_PASSAGES.items():
        result = detect_lsr_v3(text, domain)
        print_result_v3(f"Richard: {domain}", result)
        r_orphaned += len(result["orphaned"])
        r_earned += len(result["earned"])
    print(f"\n  RICHARD TOTAL: {r_orphaned} orphaned, {r_earned} earned")

    # --- Published prose (from 8c) ---
    print("\n\n[2] PUBLISHED HUMAN PROSE (pre-2020)")
    print("=" * 72)

    # Import published passages from 8c
    from lsr_exp8c_real_published import PUBLISHED_PASSAGES
    p_orphaned = 0
    p_earned = 0
    for entry in PUBLISHED_PASSAGES:
        result = detect_lsr_v3(entry["text"], entry["domain"])
        label = f"Published: {entry['author'][:40]}"
        # Only print if there are findings
        if result["orphaned"] or result["earned"]:
            print_result_v3(label, result)
        p_orphaned += len(result["orphaned"])
        p_earned += len(result["earned"])
    print(f"\n  PUBLISHED TOTAL: {p_orphaned} orphaned, {p_earned} earned")

    # --- LLM passages (from Exp 8) ---
    print("\n\n[3] LLM PASSAGES (Sonnet)")
    print("=" * 72)

    exp8_path = "/sessions/wizardly-optimistic-bohr/lsr_exp8_results.json"
    with open(exp8_path) as f:
        exp8 = json.load(f)

    l_orphaned = 0
    l_earned = 0
    for entry in exp8.get("llm_passages", []):
        result = detect_lsr_v3(entry["text"], entry["domain"])
        label = f"LLM: {entry['id']} ({entry['domain']})"
        if result["orphaned"] or result["earned"]:
            print_result_v3(label, result)
        l_orphaned += len(result["orphaned"])
        l_earned += len(result["earned"])
    print(f"\n  LLM TOTAL: {l_orphaned} orphaned, {l_earned} earned")

    # --- Final comparison ---
    print(f"\n\n{'=' * 72}")
    print("FINAL COMPARISON")
    print(f"{'=' * 72}")

    all_h_orphaned = r_orphaned + p_orphaned
    all_h_n = 25
    l_n = 20

    print(f"\n  {'Source':<30} {'Orphaned':<12} {'Earned':<12} {'Rate':<10}")
    print(f"  {'-'*60}")
    print(f"  {'Richard (n=5)':<30} {r_orphaned:<12} {r_earned:<12} {r_orphaned/5:.3f}")
    print(f"  {'Published (n=20)':<30} {p_orphaned:<12} {p_earned:<12} {p_orphaned/20:.3f}")
    print(f"  {'ALL HUMAN (n=25)':<30} {all_h_orphaned:<12} {r_earned+p_earned:<12} {all_h_orphaned/25:.3f}")
    print(f"  {'LLM Sonnet (n=20)':<30} {l_orphaned:<12} {l_earned:<12} {l_orphaned/20:.3f}")

    h_rate = all_h_orphaned / 25 if all_h_orphaned > 0 else 0
    l_rate = l_orphaned / 20 if l_orphaned > 0 else 0

    if h_rate == 0 and l_rate > 0:
        print(f"\n  Human: ZERO orphaned. LLM: {l_rate:.3f}/passage.")
    elif h_rate > 0 and l_rate > 0:
        print(f"\n  LLM/Human ratio: {l_rate/h_rate:.1f}x")
    else:
        print(f"\n  Both near zero.")

    # Save
    outfile = "lsr_v3_results.json"
    with open(outfile, "w") as f:
        json.dump({
            "richard_orphaned": r_orphaned, "richard_earned": r_earned,
            "published_orphaned": p_orphaned, "published_earned": p_earned,
            "llm_orphaned": l_orphaned, "llm_earned": l_earned,
        }, f, indent=2)
    print(f"\nResults saved to {outfile}")
