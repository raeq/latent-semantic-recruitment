#!/usr/bin/env python3
"""
LSR Experiment 5: Prompt Manipulation

Tests whether dual-meaning register alignment varies with figurative register
intensity in the prompt. Three conditions, same base story scenario:

  A. SUPPRESSED: "Write in plain, literal, technical prose. No metaphors,
     no figurative language."
  B. NEUTRAL: Standard creative writing prompt, no register instruction.
  C. AMPLIFIED: "Write in richly figurative, metaphor-heavy prose. Use
     extended metaphor throughout."

Each condition uses the same five story scenarios (strong natural registers):
  1. Sawmill / woodworking
  2. Ocean storm / sailing
  3. Kitchen fire / cooking
  4. Battlefield surgery / field medicine
  5. Blacksmith / forge work

For each generated passage, we:
  1. Extract all content words (nouns, verbs, adjectives, adverbs)
  2. Look up polysemy counts (number of WordNet synsets)
  3. For polysemous words (2+ senses), check whether any secondary sense
     belongs to the active figurative register's semantic field
  4. Compute the dual-meaning alignment rate (DMAR):
     DMAR = (polysemous words with register-aligned secondary sense) /
            (total polysemous content words)

Kill condition: No significant difference in DMAR across conditions A, B, C.
If explicit register suppression doesn't reduce LSR, it's not register-activated.

Confirmation condition: DMAR_A < DMAR_B < DMAR_C (monotonic increase with
register intensity). Dose-response relationship.

NOTE: This experiment uses Claude (via this script's own generation) as the
test subject. We generate passages by writing prompts to a file, then the
human runs them through an LLM and pastes results back. OR we use a local
model. The analysis pipeline is what this script builds.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
import re
import os
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional

# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIOS = {
    "sawmill": {
        "setting": "A worker operating a large bandsaw in a timber mill, "
                   "processing raw logs into planks during a long shift.",
        "register_fields": {
            # Semantic fields that the sawmill register activates
            "cutting": {"cut", "saw", "blade", "edge", "sharp", "slice",
                       "sever", "cleave", "rip", "tear", "split"},
            "wood": {"grain", "knot", "bark", "ring", "board", "plank",
                    "timber", "log", "sap", "pitch", "heartwood"},
            "machinery": {"feed", "drive", "belt", "gear", "teeth", "bit",
                         "chuck", "spindle", "bearing", "shaft", "motor"},
            "consumption": {"eat", "bite", "chew", "gnaw", "devour",
                          "swallow", "digest", "appetite", "hunger", "fed"},
            "violence": {"wound", "scar", "flesh", "bone", "blood",
                        "raw", "strip", "flay"},
        },
        # Words whose PRIMARY sense is sawmill-related (not dual-meaning)
        "primary_domain_words": {
            "saw", "blade", "log", "plank", "timber", "sawdust", "mill",
            "lumber", "bandsaw", "woodworking", "carpenter",
        },
    },
    "ocean_storm": {
        "setting": "A small fishing boat crew fighting through a severe storm "
                   "at sea, waves breaking over the gunwales, trying to reach "
                   "harbor.",
        "register_fields": {
            "water": {"wave", "swell", "surge", "flood", "pour", "wash",
                     "tide", "current", "drift", "flow", "stream"},
            "wind": {"gust", "blast", "blow", "gale", "howl", "scream",
                    "whistle", "roar", "lash", "whip"},
            "violence": {"pound", "batter", "beat", "strike", "lash",
                        "pummel", "assault", "hammer", "crush"},
            "swallowing": {"swallow", "gulp", "drink", "drown", "consume",
                          "devour", "engulf", "overwhelm"},
            "rope_sail": {"line", "sheet", "haul", "trim", "run",
                         "slack", "fast", "secure", "cleat"},
        },
        "primary_domain_words": {
            "boat", "ship", "sail", "mast", "hull", "deck", "bow", "stern",
            "port", "starboard", "anchor", "rudder", "helm", "ocean", "sea",
        },
    },
    "kitchen_fire": {
        "setting": "A professional chef working the line during a Friday night "
                   "rush, managing multiple burners and a wood-fired oven, "
                   "orders backing up.",
        "register_fields": {
            "fire": {"burn", "flame", "blaze", "sear", "char", "smoke",
                    "ash", "ember", "flare", "scorch", "ignite"},
            "heat": {"hot", "heat", "warm", "boil", "simmer", "sweat",
                    "steam", "roast", "bake", "broil"},
            "cutting": {"chop", "dice", "mince", "slice", "carve",
                       "fillet", "bone", "trim", "pare"},
            "violence_pressure": {"crush", "pound", "press", "squeeze",
                                 "crack", "snap", "break", "smash",
                                 "whip", "beat"},
            "body": {"skin", "flesh", "bone", "fat", "blood", "vein",
                    "breast", "leg", "neck", "tongue"},
        },
        "primary_domain_words": {
            "kitchen", "chef", "oven", "stove", "pan", "pot", "burner",
            "grill", "plate", "dish", "recipe", "cook",
        },
    },
    "battlefield_surgery": {
        "setting": "A field medic performing emergency surgery in a makeshift "
                   "tent near the front line, supplies running low, artillery "
                   "audible in the distance.",
        "register_fields": {
            "cutting": {"cut", "incision", "slice", "open", "sever",
                       "excise", "lance", "probe", "dig"},
            "body": {"flesh", "bone", "blood", "skin", "muscle", "nerve",
                    "vein", "artery", "wound", "organ", "tissue"},
            "war": {"battle", "fight", "shell", "blast", "hit",
                   "strike", "fire", "round", "shot", "target"},
            "repair": {"stitch", "bind", "tie", "close", "seal",
                      "patch", "mend", "fix", "hold"},
            "death": {"die", "dead", "kill", "lose", "gone", "fade",
                     "slip", "cold", "still", "quiet"},
        },
        "primary_domain_words": {
            "surgeon", "surgery", "scalpel", "suture", "tourniquet",
            "bandage", "morphine", "medic", "ambulance", "triage",
        },
    },
    "blacksmith": {
        "setting": "A blacksmith forging a complex tool in a rural smithy, "
                   "working the metal through multiple heats, shaping it on "
                   "the anvil.",
        "register_fields": {
            "fire_heat": {"fire", "burn", "flame", "glow", "ember",
                         "coal", "hot", "heat", "warm", "red", "white",
                         "cool", "quench"},
            "striking": {"strike", "hit", "hammer", "pound", "beat",
                        "blow", "ring", "peal", "clang", "clash"},
            "shaping": {"bend", "twist", "draw", "fold", "turn",
                       "form", "shape", "work", "fashion", "forge"},
            "metal": {"iron", "steel", "temper", "hard", "soft",
                     "brittle", "tough", "edge", "point", "flat"},
            "body_effort": {"sweat", "arm", "shoulder", "grip",
                           "muscle", "breath", "strain", "heave"},
        },
        "primary_domain_words": {
            "blacksmith", "smithy", "anvil", "forge", "bellows", "tongs",
            "quench", "ingot",
        },
    },
}


# ============================================================================
# PROMPT GENERATION
# ============================================================================

def generate_prompts() -> Dict[str, Dict[str, str]]:
    """Generate the three prompt conditions for each scenario."""
    prompts = {}

    for scenario_id, scenario in SCENARIOS.items():
        setting = scenario["setting"]

        prompts[scenario_id] = {
            "suppressed": (
                f"Write a 200-300 word passage about the following scene. "
                f"Use plain, literal, technical prose throughout. Do not use "
                f"any metaphors, similes, personification, or figurative "
                f"language of any kind. Describe only what is physically "
                f"happening in concrete, factual terms.\n\n"
                f"Scene: {setting}"
            ),
            "neutral": (
                f"Write a 200-300 word passage about the following scene. "
                f"Write in a close third-person perspective.\n\n"
                f"Scene: {setting}"
            ),
            "amplified": (
                f"Write a 200-300 word passage about the following scene. "
                f"Write in richly figurative prose. Use extended metaphor "
                f"throughout. Let the imagery of the setting bleed into "
                f"every description. Personify tools, materials, and forces "
                f"of nature. The prose should be dense with figurative "
                f"language.\n\n"
                f"Scene: {setting}"
            ),
        }

    return prompts


# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

# Simple POS-like content word filter (no NLTK dependency)
# We'll use a stopword list and heuristics
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "must", "it", "its", "he", "she", "they", "them", "their", "his",
    "her", "him", "we", "us", "our", "you", "your", "i", "my", "me",
    "this", "that", "these", "those", "which", "who", "whom", "what",
    "where", "when", "how", "why", "if", "then", "than", "so", "not",
    "no", "nor", "too", "very", "just", "also", "still", "even", "now",
    "here", "there", "up", "out", "off", "over", "into", "onto", "upon",
    "about", "after", "before", "during", "between", "through", "under",
    "above", "below", "each", "every", "all", "both", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "while",
    "until", "because", "since", "although", "though", "whether",
    "either", "neither", "yet", "already", "again", "once", "twice",
    "enough", "much", "many", "several", "another", "any", "anything",
    "everything", "nothing", "something", "someone", "everyone", "anyone",
    "himself", "herself", "itself", "themselves", "itself",
}

# Punctuation to strip
PUNCT = re.compile(r'[^a-zA-Z]')


def extract_content_words(text: str) -> List[str]:
    """Extract content words from text, lowercased, stopwords removed."""
    words = text.lower().split()
    content = []
    for w in words:
        cleaned = PUNCT.sub('', w)
        if cleaned and len(cleaned) > 2 and cleaned not in STOPWORDS:
            content.append(cleaned)
    return content


def check_register_alignment(word: str, register_fields: Dict[str, Set[str]],
                              primary_words: Set[str]) -> Tuple[bool, List[str]]:
    """
    Check if a word appears in any register field.

    Returns (is_aligned, list_of_matching_fields).

    Excludes words whose PRIMARY sense is domain-specific (e.g., 'saw' in
    a sawmill scene is not dual-meaning — it's literal).
    """
    if word in primary_words:
        return False, []

    matched_fields = []
    for field_name, field_words in register_fields.items():
        if word in field_words:
            matched_fields.append(field_name)

    return len(matched_fields) > 0, matched_fields


def is_polysemous(word: str) -> bool:
    """
    Heuristic polysemy check. Without WordNet, we use a curated list of
    known polysemous words that commonly appear in these registers.

    In a production version, this would use NLTK WordNet synset counts.
    For the experiment, we maintain an explicit list so results are
    reproducible and auditable.
    """
    return word in POLYSEMOUS_WORDS


# Curated set of polysemous words likely to appear in these scenarios.
# Each has 2+ distinct senses in standard dictionaries.
# This is NOT exhaustive — it's the measurement instrument.
# A word is included if it has a clear primary sense AND a clear
# secondary sense that could align with one of our register fields.
POLYSEMOUS_WORDS = {
    # Body/violence dual meanings
    "bit", "teeth", "fed", "feed", "tongue", "mouth", "lip", "arm",
    "shoulder", "back", "face", "head", "heart", "eye", "neck", "bone",
    "skin", "flesh", "blood", "vein", "muscle", "nerve", "grip",
    "breast", "leg", "fat",

    # Cutting/violence dual meanings
    "cut", "sharp", "edge", "point", "blade", "slash", "slice", "split",
    "tear", "rip", "sever", "break", "snap", "crack", "crush",
    "strike", "hit", "beat", "pound", "hammer",

    # Fire/heat dual meanings
    "burn", "fire", "flame", "blaze", "glow", "spark", "flash",
    "flare", "scorch", "sear", "smoke", "ash", "ember", "char",
    "hot", "cool", "warm", "temper", "forge",

    # Water/weather dual meanings
    "wave", "flood", "pour", "wash", "tide", "current", "drift",
    "flow", "stream", "surge", "swell", "drown", "sink", "rise",
    "blow", "gust", "blast", "storm", "howl", "roar", "lash",

    # Machinery/work dual meanings
    "drive", "gear", "belt", "shaft", "bearing", "chuck", "run",
    "turn", "draw", "press", "work", "strain", "grind",

    # Consumption dual meanings
    "swallow", "gulp", "drink", "devour", "consume", "digest",
    "appetite", "taste", "raw", "tender", "rich", "dry",

    # Rope/line dual meanings
    "line", "fast", "sheet", "haul", "trim", "slack", "secure",

    # Shaping/forming dual meanings
    "bend", "twist", "fold", "form", "shape", "fashion", "mold",
    "cast", "ring", "flat",

    # Death/ending dual meanings
    "dead", "still", "cold", "quiet", "fade", "slip", "gone", "lose",
    "fall", "drop", "sink", "end",

    # General high-polysemy words
    "set", "run", "light", "right", "left", "bank", "spring",
    "pitch", "check", "bar", "close", "deep", "hard", "soft",
    "bright", "dark", "heavy", "rough", "smooth", "thick", "thin",
    "sound", "clear", "fresh", "green", "board", "stock", "plant",
}


def analyze_passage(text: str, scenario_id: str) -> Dict:
    """
    Analyze a single passage for dual-meaning register alignment.

    Returns dict with:
      - total_words: total content words
      - polysemous_words: list of polysemous content words found
      - aligned_words: list of (word, fields) where secondary sense aligns
      - dmar: dual-meaning alignment rate
      - raw_alignment_count: count of aligned words
      - raw_polysemous_count: count of polysemous words
    """
    scenario = SCENARIOS[scenario_id]
    register_fields = scenario["register_fields"]
    primary_words = scenario["primary_domain_words"]

    content_words = extract_content_words(text)
    total = len(content_words)

    polysemous_found = []
    aligned_found = []

    for word in content_words:
        if is_polysemous(word):
            polysemous_found.append(word)
            is_aligned, fields = check_register_alignment(
                word, register_fields, primary_words
            )
            if is_aligned:
                aligned_found.append((word, fields))

    poly_count = len(polysemous_found)
    aligned_count = len(aligned_found)
    dmar = aligned_count / poly_count if poly_count > 0 else 0.0

    return {
        "total_content_words": total,
        "polysemous_count": poly_count,
        "aligned_count": aligned_count,
        "dmar": dmar,
        "polysemy_rate": poly_count / total if total > 0 else 0.0,
        "polysemous_words": polysemous_found,
        "aligned_words": aligned_found,
    }


# ============================================================================
# RESULTS AGGREGATION
# ============================================================================

def aggregate_results(results: Dict[str, Dict[str, Dict]]) -> Dict:
    """
    Aggregate results across scenarios for each condition.

    Input structure: results[scenario_id][condition] = analysis_dict
    """
    conditions = ["suppressed", "neutral", "amplified"]
    agg = {}

    for condition in conditions:
        dmars = []
        poly_rates = []
        total_aligned = 0
        total_poly = 0
        total_words = 0

        for scenario_id in SCENARIOS:
            if scenario_id in results and condition in results[scenario_id]:
                r = results[scenario_id][condition]
                dmars.append(r["dmar"])
                poly_rates.append(r["polysemy_rate"])
                total_aligned += r["aligned_count"]
                total_poly += r["polysemous_count"]
                total_words += r["total_content_words"]

        n = len(dmars)
        if n > 0:
            mean_dmar = sum(dmars) / n
            mean_poly_rate = sum(poly_rates) / n
            pooled_dmar = total_aligned / total_poly if total_poly > 0 else 0.0
        else:
            mean_dmar = 0.0
            mean_poly_rate = 0.0
            pooled_dmar = 0.0

        agg[condition] = {
            "n_scenarios": n,
            "mean_dmar": mean_dmar,
            "pooled_dmar": pooled_dmar,
            "mean_polysemy_rate": mean_poly_rate,
            "total_aligned": total_aligned,
            "total_polysemous": total_poly,
            "total_content_words": total_words,
            "individual_dmars": dmars,
        }

    return agg


def print_results(results: Dict[str, Dict[str, Dict]], agg: Dict):
    """Print formatted results."""
    print("=" * 72)
    print("EXPERIMENT 5: PROMPT MANIPULATION — RESULTS")
    print("=" * 72)

    conditions = ["suppressed", "neutral", "amplified"]

    # Per-scenario detail
    for scenario_id in SCENARIOS:
        print(f"\n--- {scenario_id.upper()} ---")
        for condition in conditions:
            if scenario_id in results and condition in results[scenario_id]:
                r = results[scenario_id][condition]
                print(f"  {condition:12s}: "
                      f"DMAR={r['dmar']:.3f}  "
                      f"aligned={r['aligned_count']:2d}/{r['polysemous_count']:2d} poly  "
                      f"({r['total_content_words']} content words, "
                      f"polysemy rate={r['polysemy_rate']:.3f})")
                if r['aligned_words']:
                    words_str = ", ".join(
                        f"{w}[{'+'.join(f)}]"
                        for w, f in r['aligned_words']
                    )
                    print(f"               aligned: {words_str}")

    # Aggregate
    print("\n" + "=" * 72)
    print("AGGREGATE RESULTS")
    print("=" * 72)

    for condition in conditions:
        a = agg[condition]
        print(f"\n  {condition.upper():12s}:")
        print(f"    Mean DMAR:      {a['mean_dmar']:.4f}")
        print(f"    Pooled DMAR:    {a['pooled_dmar']:.4f}")
        print(f"    Mean poly rate: {a['mean_polysemy_rate']:.4f}")
        print(f"    Total aligned:  {a['total_aligned']}")
        print(f"    Total poly:     {a['total_polysemous']}")
        print(f"    Total words:    {a['total_content_words']}")
        print(f"    Per-scenario:   {a['individual_dmars']}")

    # Kill condition assessment
    print("\n" + "=" * 72)
    print("KILL CONDITION ASSESSMENT")
    print("=" * 72)

    s_dmar = agg["suppressed"]["pooled_dmar"]
    n_dmar = agg["neutral"]["pooled_dmar"]
    a_dmar = agg["amplified"]["pooled_dmar"]

    print(f"\n  Suppressed pooled DMAR: {s_dmar:.4f}")
    print(f"  Neutral pooled DMAR:    {n_dmar:.4f}")
    print(f"  Amplified pooled DMAR:  {a_dmar:.4f}")

    if s_dmar < n_dmar < a_dmar:
        print("\n  RESULT: Monotonic increase (S < N < A). "
              "Dose-response relationship observed.")
        print("  LSR SURVIVES this kill condition.")
        ratio = a_dmar / s_dmar if s_dmar > 0 else float('inf')
        print(f"  Amplified/Suppressed ratio: {ratio:.2f}x")
    elif abs(s_dmar - a_dmar) < 0.02:
        print("\n  RESULT: No meaningful difference between conditions.")
        print("  LSR KILLED. Register manipulation doesn't affect alignment.")
    else:
        print(f"\n  RESULT: Non-monotonic pattern.")
        print("  LSR INCONCLUSIVE. Pattern doesn't match prediction.")

    # Additional diagnostic
    print("\n--- Additional diagnostics ---")
    s_poly = agg["suppressed"]["mean_polysemy_rate"]
    n_poly = agg["neutral"]["mean_polysemy_rate"]
    a_poly = agg["amplified"]["mean_polysemy_rate"]
    print(f"  Polysemy rate (suppressed): {s_poly:.4f}")
    print(f"  Polysemy rate (neutral):    {n_poly:.4f}")
    print(f"  Polysemy rate (amplified):  {a_poly:.4f}")
    if s_poly < n_poly < a_poly:
        print("  Polysemy rate also increases with register intensity.")
        print("  Consistent with LSR (more figurative = more polysemous words).")
    else:
        print("  Polysemy rate does NOT monotonically increase.")
        print("  If DMAR increases but polysemy rate doesn't, the effect is")
        print("  in alignment specificity, not just polysemy volume.")


# ============================================================================
# PASSAGE MANAGEMENT (load/save)
# ============================================================================

PASSAGES_FILE = "lsr_exp5_passages.json"


def save_passages(passages: Dict[str, Dict[str, str]], filepath: str = None):
    """Save generated/collected passages to JSON."""
    if filepath is None:
        filepath = PASSAGES_FILE
    with open(filepath, 'w') as f:
        json.dump(passages, f, indent=2)
    print(f"Passages saved to {filepath}")


def load_passages(filepath: str = None) -> Dict[str, Dict[str, str]]:
    """Load passages from JSON."""
    if filepath is None:
        filepath = PASSAGES_FILE
    with open(filepath, 'r') as f:
        return json.load(f)


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "prompts":
        # Generate and display prompts for manual LLM runs
        prompts = generate_prompts()
        print("=" * 72)
        print("EXPERIMENT 5: PROMPTS FOR LLM GENERATION")
        print("=" * 72)
        for scenario_id, conditions in prompts.items():
            for condition, prompt in conditions.items():
                print(f"\n--- {scenario_id} / {condition} ---")
                print(prompt)
                print()
        # Also save prompts
        with open("lsr_exp5_prompts.json", 'w') as f:
            json.dump(prompts, f, indent=2)
        print("Prompts saved to lsr_exp5_prompts.json")

    elif len(sys.argv) > 1 and sys.argv[1] == "analyze":
        # Analyze saved passages
        filepath = sys.argv[2] if len(sys.argv) > 2 else PASSAGES_FILE
        passages = load_passages(filepath)

        results = {}
        for scenario_id in SCENARIOS:
            results[scenario_id] = {}
            for condition in ["suppressed", "neutral", "amplified"]:
                if scenario_id in passages and condition in passages[scenario_id]:
                    text = passages[scenario_id][condition]
                    results[scenario_id][condition] = analyze_passage(
                        text, scenario_id
                    )

        agg = aggregate_results(results)
        print_results(results, agg)

    elif len(sys.argv) > 1 and sys.argv[1] == "self-test":
        # Run analysis on built-in test passages to verify the pipeline
        print("Running pipeline self-test with synthetic passages...")
        test_passages = {
            "sawmill": {
                "suppressed": (
                    "The operator positioned the log on the carriage and "
                    "engaged the mechanism. The bandsaw moved through the "
                    "wood at a consistent rate. Sawdust accumulated below "
                    "the cutting surface. He adjusted the guide and made "
                    "another pass. The plank separated cleanly."
                ),
                "neutral": (
                    "He fed the log into the bandsaw and watched it bite "
                    "through the grain. The teeth found the heartwood and "
                    "the whole machine shuddered. Sawdust fell like dry "
                    "snow. His arms ached from the shift but the blade "
                    "was sharp and hungry and the work had its own pull."
                ),
                "amplified": (
                    "The saw fed on the timber like something starved. Its "
                    "teeth bit deep into the grain, tearing through rings "
                    "that had taken decades to form. The log screamed as the "
                    "blade devoured it, splitting flesh from bone, ripping "
                    "heartwood from sapwood. Sawdust bled from every wound. "
                    "He gripped the controls and let the machine swallow "
                    "another length, its appetite endless, its tongue of "
                    "steel sharp enough to taste the difference between "
                    "green wood and dry."
                ),
            },
        }

        results = {}
        for scenario_id in test_passages:
            results[scenario_id] = {}
            for condition in ["suppressed", "neutral", "amplified"]:
                text = test_passages[scenario_id][condition]
                results[scenario_id][condition] = analyze_passage(
                    text, scenario_id
                )

        agg = aggregate_results(results)
        print_results(results, agg)

    else:
        print("Usage:")
        print("  python3 lsr_experiment_5.py prompts    — Generate LLM prompts")
        print("  python3 lsr_experiment_5.py analyze     — Analyze saved passages")
        print("  python3 lsr_experiment_5.py self-test   — Run pipeline self-test")
        print()
        print("Workflow:")
        print("  1. Run 'prompts' to generate the 15 prompts")
        print("  2. Feed each prompt to the target LLM")
        print("  3. Save results in lsr_exp5_passages.json")
        print("  4. Run 'analyze' to compute DMAR scores")


if __name__ == "__main__":
    main()
