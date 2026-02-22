#!/usr/bin/env python3
"""
LSR Detector: Unjustified Figurative Polysemy

Operationalizes the detection heuristic from Experiment 1b:

  1. Identify polysemous content words
  2. Check if secondary sense aligns with passage register
  3. Check if a justifying metaphorical frame exists in context
  4. Flag unjustified cases as LSR candidates

Step 3 is the hard one. "Justifying frame" means:
  - Explicit metaphor signpost within 2-3 sentences
    ("like a", "as if", "it was a [metaphor]", "that's X, that is")
  - Established extended metaphor (once opened, subsequent figurative
    words within it are justified)
  - Structural position as punchline (final sentence of passage,
    preceded by literal buildup)

This is a heuristic detector, not a classifier. It produces CANDIDATES
for human review, not verdicts.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import re
from typing import Dict, List, Tuple, Set, Optional


# ============================================================================
# REGISTER DEFINITIONS (from Experiment 5)
# ============================================================================

REGISTER_FIELDS = {
    "body_consumption": {
        "fed", "feed", "bit", "bite", "teeth", "tongue", "mouth", "lip",
        "swallow", "gulp", "devour", "consume", "appetite", "taste",
        "hunger", "starve", "chew", "gnaw", "digest", "eat", "ate",
        "stomach", "throat", "raw",
    },
    "body_parts": {
        "arm", "shoulder", "back", "face", "head", "heart", "eye", "neck",
        "bone", "skin", "flesh", "blood", "vein", "muscle", "nerve",
        "grip", "breast", "leg", "fat", "fist",
    },
    "cutting_violence": {
        "cut", "sharp", "edge", "point", "blade", "slash", "slice", "split",
        "tear", "rip", "sever", "break", "snap", "crack", "crush",
        "strike", "hit", "beat", "pound", "hammer", "wound", "scar",
    },
    "fire_heat": {
        "burn", "fire", "flame", "blaze", "glow", "spark", "flash",
        "flare", "scorch", "sear", "smoke", "ash", "ember", "char",
        "hot", "cool", "warm", "temper", "forge", "roast", "smelt",
    },
    "water_weather": {
        "wave", "flood", "pour", "wash", "tide", "current", "drift",
        "flow", "stream", "surge", "swell", "drown", "sink", "rise",
        "blow", "gust", "blast", "storm", "howl", "roar", "lash",
    },
    "personification": {
        "stubborn", "listen", "want", "wanted", "refuse", "willing",
        "angry", "hungry", "thirsty", "tired", "patient", "eager",
        "reluctant", "obey", "resist", "yield", "surrender", "forgive",
        "complain", "scream", "whisper", "sing", "cry", "weep",
        "breathe", "sleep", "wake", "dream", "die", "live",
    },
    "death_ending": {
        "dead", "death", "die", "kill", "gone", "fade", "slip",
        "cold", "still", "quiet", "fall", "drop", "end", "last",
    },
}

# Polysemous words (from Experiment 5, curated list)
POLYSEMOUS_WORDS = {
    "bit", "teeth", "fed", "feed", "tongue", "mouth", "lip", "arm",
    "shoulder", "back", "face", "head", "heart", "eye", "neck", "bone",
    "skin", "flesh", "blood", "vein", "muscle", "nerve", "grip",
    "breast", "leg", "fat", "cut", "sharp", "edge", "point", "blade",
    "slash", "slice", "split", "tear", "rip", "sever", "break", "snap",
    "crack", "crush", "strike", "hit", "beat", "pound", "hammer",
    "burn", "fire", "flame", "blaze", "glow", "spark", "flash",
    "flare", "scorch", "sear", "smoke", "ash", "ember", "char",
    "hot", "cool", "warm", "temper", "forge", "wave", "flood", "pour",
    "wash", "tide", "current", "drift", "flow", "stream", "surge",
    "swell", "drown", "sink", "rise", "blow", "gust", "blast", "storm",
    "howl", "roar", "lash", "drive", "gear", "belt", "shaft", "bearing",
    "chuck", "run", "turn", "draw", "press", "work", "strain", "grind",
    "swallow", "gulp", "drink", "devour", "consume", "digest",
    "appetite", "taste", "raw", "tender", "rich", "dry", "line",
    "fast", "sheet", "haul", "trim", "slack", "secure", "bend",
    "twist", "fold", "form", "shape", "fashion", "mold", "cast",
    "ring", "flat", "dead", "still", "cold", "quiet", "fade", "slip",
    "gone", "lose", "fall", "drop", "end", "set", "light", "right",
    "left", "bank", "spring", "pitch", "check", "bar", "close", "deep",
    "hard", "soft", "bright", "dark", "heavy", "rough", "smooth",
    "thick", "thin", "sound", "clear", "fresh", "green", "board",
    "stock", "plant", "stubborn", "listen", "fist", "wound", "scar",
    "roast", "death", "die", "surrender", "rage",
}

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
    "enough", "much", "many", "several", "another", "any",
}

# Metaphor signpost patterns (regex)
SIGNPOST_PATTERNS = [
    r'\blike\s+(?:a|an|the)\b',           # "like a [noun]"
    r'\bas\s+(?:if|though)\b',             # "as if", "as though"
    r'\bwas\s+(?:a|an)\b',                 # "was a [metaphor]"
    r'\bthat\'s\b',                         # "that's [metaphor], that is"
    r'\bthe\s+way\s+(?:a|an)\b',           # "the way a [comparison]"
    r'\breminded\s+(?:him|her|them)\s+of\b',  # "reminded X of"
    r'\blike\s+something\b',                # "like something [adj]"
    r'\bnothing\s+more\s+than\b',           # "nothing more than"
    r'\bwhat\s+(?:a|an)\b',                 # "what a [metaphor]"
]


PUNCT = re.compile(r'[^a-zA-Z\']')


def detect_lsr(text: str, domain_primary_words: Set[str] = None) -> List[Dict]:
    """
    Scan text for LSR candidates: unjustified figurative polysemous words.

    Returns list of candidate dicts with:
      - word: the flagged word
      - sentence: the sentence containing it
      - register_fields: which register fields match
      - has_signpost: whether a metaphor signpost exists nearby
      - position: word's position in the passage (early/mid/terminal)
      - verdict: "LSR_CANDIDATE" or "PROBABLY_JUSTIFIED"
    """
    if domain_primary_words is None:
        domain_primary_words = set()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    total_sentences = len(sentences)

    candidates = []

    for sent_idx, sentence in enumerate(sentences):
        words = sentence.lower().split()
        for word_raw in words:
            word = PUNCT.sub('', word_raw).lower()

            if not word or len(word) < 3:
                continue
            if word in STOPWORDS:
                continue
            if word not in POLYSEMOUS_WORDS:
                continue
            if word in domain_primary_words:
                continue

            # Check register alignment
            matched_fields = []
            for field_name, field_words in REGISTER_FIELDS.items():
                if word in field_words:
                    matched_fields.append(field_name)

            if not matched_fields:
                continue

            # Check for metaphor signpost in surrounding context
            # (current sentence + 1 sentence before + 1 after)
            context_start = max(0, sent_idx - 1)
            context_end = min(total_sentences, sent_idx + 2)
            context = " ".join(sentences[context_start:context_end]).lower()

            has_signpost = False
            for pattern in SIGNPOST_PATTERNS:
                if re.search(pattern, context):
                    has_signpost = True
                    break

            # Check position (terminal = last 2 sentences)
            is_terminal = sent_idx >= total_sentences - 2

            # Verdict
            if has_signpost:
                verdict = "PROBABLY_JUSTIFIED"
            else:
                verdict = "LSR_CANDIDATE"

            candidates.append({
                "word": word,
                "sentence": sentence.strip(),
                "register_fields": matched_fields,
                "has_signpost": has_signpost,
                "is_terminal": is_terminal,
                "sentence_position": f"{sent_idx + 1}/{total_sentences}",
                "verdict": verdict,
            })

    return candidates


def scan_passage(text: str, label: str, domain_primary: Set[str] = None):
    """Scan a passage and print results."""
    candidates = detect_lsr(text, domain_primary)

    lsr = [c for c in candidates if c["verdict"] == "LSR_CANDIDATE"]
    justified = [c for c in candidates if c["verdict"] == "PROBABLY_JUSTIFIED"]

    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  LSR candidates: {len(lsr)}  |  Probably justified: {len(justified)}")
    print(f"{'=' * 60}")

    for c in candidates:
        marker = ">>> LSR" if c["verdict"] == "LSR_CANDIDATE" else "    ok "
        pos = "TERMINAL" if c["is_terminal"] else f"sent {c['sentence_position']}"
        print(f"\n  {marker}  '{c['word']}' [{', '.join(c['register_fields'])}]")
        print(f"          position: {pos}")
        print(f"          signpost: {'YES' if c['has_signpost'] else 'NO'}")
        print(f"          \"{c['sentence'][:100]}...\"" if len(c["sentence"]) > 100
              else f"          \"{c['sentence']}\"")

    return candidates


# ============================================================================
# RUN ON ALL EXPERIMENT 5 PASSAGES
# ============================================================================

if __name__ == "__main__":
    import json
    import os

    passages_file = "lsr_exp5_passages.json"
    if not os.path.exists(passages_file):
        passages_file = os.path.join(
            "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld",
            "lsr_exp5_passages.json"
        )

    with open(passages_file) as f:
        passages = json.load(f)

    # Domain primary words (literal, not dual-meaning in their domain)
    primary = {
        "sawmill": {"saw", "blade", "log", "plank", "timber", "sawdust",
                    "mill", "lumber", "bandsaw", "carpenter"},
        "ocean_storm": {"boat", "ship", "sail", "mast", "hull", "deck",
                       "bow", "stern", "anchor", "rudder", "helm", "ocean",
                       "sea", "harbor"},
        "kitchen_fire": {"kitchen", "chef", "oven", "stove", "pan", "pot",
                        "burner", "grill", "plate", "dish", "cook"},
        "battlefield_surgery": {"surgeon", "surgery", "scalpel", "suture",
                               "tourniquet", "bandage", "morphine", "medic",
                               "triage"},
        "blacksmith": {"blacksmith", "smithy", "anvil", "tongs",
                      "quench", "ingot", "bellows"},
    }

    total_lsr = {"suppressed": 0, "neutral": 0, "amplified": 0}
    total_justified = {"suppressed": 0, "neutral": 0, "amplified": 0}

    for scenario_id in passages:
        for condition in ["suppressed", "neutral", "amplified"]:
            text = passages[scenario_id][condition]
            label = f"{scenario_id} / {condition}"
            candidates = scan_passage(text, label, primary.get(scenario_id, set()))
            lsr = len([c for c in candidates if c["verdict"] == "LSR_CANDIDATE"])
            just = len([c for c in candidates if c["verdict"] == "PROBABLY_JUSTIFIED"])
            total_lsr[condition] += lsr
            total_justified[condition] += just

    print("\n\n" + "=" * 60)
    print("AGGREGATE: LSR CANDIDATES BY CONDITION")
    print("=" * 60)
    for condition in ["suppressed", "neutral", "amplified"]:
        print(f"  {condition:12s}: {total_lsr[condition]} LSR candidates, "
              f"{total_justified[condition]} probably justified")

    print(f"""
  If the detector works:
    - Suppressed should have fewest LSR candidates
    - Amplified should have most
    - The justified count should also rise with amplification
      (more metaphor signposts in more figurative prose)
    """)

    # Now scan Richard's passages
    print("\n" + "=" * 60)
    print("HUMAN PASSAGES (Richard)")
    print("=" * 60)

    richard_passages = {
        "sawmill": (
            "I was working in the mill last week. The timber mill down on the "
            "river, where It's always been. The tree trunks came in, delivered "
            "by oxen as usual. Stacked as usual. Nothing new, nothing strange. "
            "just another day sawing trunks into lumber for use by all kinds "
            "of people. The first trunk came in. It was shaved of branches, "
            "naturally, otherwise how could it have been delivered here? "
            "6 Strong men heaved it onto the sawing frame. We call her Big "
            "Bertha cause she's big, and Bertha because she demands all our "
            "love before she'll provide what we want. The first trunk was no "
            "problem as expected. Onto the frame. Lock it in. Bertha did most "
            "of the rest drawing the bed fore, activating the band saw, "
            "pulling the bed back, cutting down one side. Always the same cut "
            "in the same location but the trunk rotates, see? Its always a "
            "different cut being made, even the the band saw never moves, "
            "only the trunk. That's life, that is. You're always the same "
            "trunk. Life shaves pieces of your health off. Still you, though. "
            "Turn left and your stamina has been taken. Turn left again and "
            "life's saw takes your strength. Left again and its your eyesight. "
            "Left again and its your heart. Keep going, and all that's "
            "remaining is your memory, until Bertha takes that, too."
        ),
        "ocean_storm": (
            "Me and the boys are out on the fish again. 5 of us, the normal "
            "crew out here in rain on the boat. Five in a boat in the rain "
            "although tonight the rain is more than rain and the wind is more "
            "than wind, it's storming right hard and I have to ask Boys! Be "
            "we turning around like, and heading home? if I'm interprering "
            "the jeering and the insults and the questioning of my manlihood, "
            "the boys would rather drown than admit that these waves are "
            "stronger than they are but I'm frightened now right proper and "
            "crash as they say, that's the mast small as it is but its all "
            "we had and now we might have to row. Are we gonna be swimming "
            "home boys? I shout. No jeering now. They want to swim even less "
            "than I do. The fish are safe at the bottom of the sea. They're "
            "only in danger once we've hauled them out of the water, up to "
            "where we are. Oh the irony. That its safe up here I'd be "
            "happier down where the fish are. Only I'd be a gonner by then."
        ),
        "kitchen_fire": (
            "9 covers in and it was 6pm on a Friday. Not good yet it should "
            "have been at least 10 covers by 6pm. Another slow night and "
            "another night of full staff. All good lads and lasses they were, "
            "some green and some yellow and some blacker than my Jamaican "
            "self. There were a bunch of us with me yelling and everyone "
            "jumping. I'm not a boss and I don't hold a whip but when "
            "there's punters to please and a business to run someone has to "
            "the shouting else everyone's being sent home for ever and never "
            "coming back to a restaurant that's closed for refurbishment "
            "when refurbishment means tax debt repayment, dispossession, "
            "foreclosure and the dole. I mean I didn't really expect the "
            "chopping and frying and freezing and punching Chef Mike to turn "
            "out any different this time to any other time. But fuck me, "
            "being a chef meant nothing more than being slowly roasted."
        ),
        "battlefield_surgery": (
            "1 2 3 punch 1 2 3 punch 1 2 3 punch although this one is a "
            "gonner. A flatliner. No real surprise with a hole in his hip "
            "I could have parked my kitchen sink in. No blood left quickly "
            "means no life left. Its axiomatic. I looked in the consultant's "
            "face. He had his watch out. He was about to call it I saw it "
            "and I saw that he didn't want to. The stats would drop another "
            "notch and another percentile would disappear from his chance "
            "at a MassGen residency. The whistles actually managed to "
            "capture my attention on beat 3 of the next cycle. The next "
            "grunt was being rushed into our crashpad. They were whistling. "
            "Code red with a chance at dying and a chance at surviving. The "
            "consultant didn't call it he screamed it Time of death 12:36! "
            "EVERYONE move over to incoming! His attention snapped across "
            "to the statistic he might yet be able to save, todays next "
            "code red."
        ),
        "blacksmith": (
            "Whollop! Turn. Whollop! Turn. Whollop! in the forge. The work "
            "piece was complicated, odd shaped, alloyed iron. It was a tough "
            "piece but it was for the Lord and it had to be right otherwise "
            "I'd have another black mark on a long list of black marks "
            "marching me towards the headsman. Keep them bellows going ya "
            "little fucker! I yelled at the apprentice. What's his name. "
            "Who cared it wasn't his neck on the line it was only his "
            "hearing if my screaming got too loud. It was hot in there that "
            "day but not hot enough to stop me from thinking about my goose "
            "in a noose if this piece wasn't done right and if it wasn't "
            "done today. It was hot again, the forge gone white from all "
            "the oxygen pumped in by what's his name. I took my tongs and "
            "grabbed it quick-like. Whallop! turn. Whallop! turn. That was "
            "my rhythm: Whallop! turn. Whallop! turn. Or it would just be "
            "Swing, back and forth. Swing."
        ),
    }

    h_total_lsr = 0
    h_total_just = 0
    for scenario_id, text in richard_passages.items():
        candidates = scan_passage(
            text,
            f"HUMAN: {scenario_id}",
            primary.get(scenario_id, set())
        )
        h_lsr = len([c for c in candidates if c["verdict"] == "LSR_CANDIDATE"])
        h_just = len([c for c in candidates if c["verdict"] == "PROBABLY_JUSTIFIED"])
        h_total_lsr += h_lsr
        h_total_just += h_just

    print(f"\n\n{'=' * 60}")
    print("FINAL COMPARISON")
    print("=" * 60)
    print(f"\n  LLM suppressed:  {total_lsr['suppressed']} LSR candidates")
    print(f"  LLM neutral:     {total_lsr['neutral']} LSR candidates")
    print(f"  LLM amplified:   {total_lsr['amplified']} LSR candidates")
    print(f"  HUMAN (Richard): {h_total_lsr} LSR candidates")
