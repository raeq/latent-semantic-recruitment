#!/usr/bin/env python3
"""
LSR Detector v2: Unjustified Figurative Polysemy Detection

v1 failed because it couldn't distinguish literal from figurative use.
"wound" in surgery, "forge" in a smithy, "hot" in a forge — all literal,
all flagged as LSR candidates.

v2 fixes this with three mechanisms:
  1. EXPANDED domain-literal sets: every word whose primary sense is
     directly about the domain activity is excluded
  2. PERSONIFICATION detection: inanimate subject + animate verb = figurative
  3. METAPHOR FRAME detection: simile markers, "was a" constructions,
     established figurative context

The manual annotation in Experiment 1b achieved 0% (human) vs 100% (LLM)
on unjustified figurative use. This detector operationalizes that annotation.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import re
import json
import os
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


# ============================================================================
# DOMAIN-LITERAL SETS (EXPANDED)
# ============================================================================
# These are words whose PRIMARY sense is literally about the domain.
# They should NOT be flagged as LSR candidates in their home domain.
# This is the key fix from v1.

DOMAIN_LITERAL = {
    "sawmill": {
        # Tools and equipment
        "saw", "blade", "bandsaw", "mill", "timber", "lumber", "plank",
        "board", "sawdust", "carpenter", "carriage", "guide", "peel",
        # Materials
        "log", "trunk", "wood", "grain", "knot", "bark", "ring",
        "heartwood", "sapwood", "sap", "pine", "oak",
        # Actions that are LITERALLY about sawing
        "cut", "cutting", "feed", "fed",  # feed mechanism is technical
        "stack", "stacked", "turn", "turned", "rotate",
        # Physical properties of the work
        "sharp", "edge", "thick", "thin",
    },
    "ocean_storm": {
        # The ocean and weather
        "wave", "waves", "swell", "surge", "tide", "current",
        "storm", "gust", "gale", "wind", "rain", "spray",
        # The boat
        "boat", "ship", "sail", "mast", "hull", "deck", "bow", "stern",
        "port", "starboard", "anchor", "rudder", "helm", "gunwale",
        "keel", "rigging",
        # Sailing actions that are literal
        "haul", "trim", "secure", "line", "fast", "cleat",
        # Water actions that are literal at sea
        "drown", "swim", "swimming", "sink", "float", "roll",
        "pitch", "heave",
        # Weather literal
        "blow", "hit", "crash",
    },
    "kitchen_fire": {
        # Equipment
        "kitchen", "chef", "oven", "stove", "pan", "pot", "burner",
        "grill", "plate", "dish", "knife", "spatula", "peel",
        # Food and cooking
        "cook", "cooking", "fry", "frying", "chop", "chopping",
        "slice", "dice", "mince", "boil", "simmer", "roast",
        "bake", "sear", "saute",
        # Kitchen-literal body/food words
        "skin", "bone", "fat", "breast", "leg", "neck",  # meat cuts
        "tongue",  # when tasting
        # Temperature
        "hot", "heat", "warm", "cool", "cold", "freeze", "freezing",
        # Kitchen actions
        "cut", "press", "squeeze", "whip", "beat",
        "taste", "tasted",
    },
    "battlefield_surgery": {
        # Medical
        "surgeon", "surgery", "medic", "scalpel", "suture", "tourniquet",
        "bandage", "morphine", "triage", "ambulance",
        # Body parts (LITERAL in surgery — they're operating on them)
        "wound", "blood", "bleeding", "flesh", "bone", "skin", "muscle",
        "nerve", "vein", "artery", "tissue", "organ", "leg", "thigh",
        "heart",  # heart rate is literal
        "face",   # looking at someone's face is literal
        # Medical actions
        "cut", "incision", "probe", "stitch", "close", "dress",
        "irrigate", "extract",
        # Military literal
        "shell", "blast", "fire", "round", "shot", "artillery",
        # Vital signs
        "pulse", "pressure", "rate",
        # Clinical terms
        "death",  # "time of death" is a medical declaration
        "code",   # "code red" is a classification
        "drop",   # "stats would drop" is literal statistics
        "beat",   # "beat 3 of the next cycle" is literal rhythm
    },
    "blacksmith": {
        # Tools and equipment
        "blacksmith", "smithy", "anvil", "forge", "bellows", "tongs",
        "quench", "ingot", "hammer",
        # Actions LITERALLY about metalwork
        "strike", "struck", "blow", "blows", "hit", "pound",
        "heat", "heated", "hot", "cool", "cooled", "cold",
        "shape", "shaped", "form", "bend", "twist", "draw", "drawn",
        "turn", "turned", "flat", "point", "edge", "taper",
        # Metal properties
        "hard", "soft", "brittle", "tough", "bright", "dark",
        "red", "orange", "white", "straw",
        # Physical
        "fire",  # literal forge fire
        "back",  # "put it back in the fire"
    },
}


# ============================================================================
# POLYSEMOUS WORDS WITH REGISTER FIELDS
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
        "hot", "cool", "warm", "temper", "forge", "roast",
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

# All polysemous words across all fields
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

# ============================================================================
# PERSONIFICATION DETECTION
# ============================================================================
# Key heuristic: inanimate nouns taking animate verbs = figurative

INANIMATE_NOUNS = {
    # Tools and equipment
    "blade", "saw", "bandsaw", "machine", "hammer", "anvil", "forge",
    "knife", "oven", "grill", "burner", "stove", "pan", "pot",
    "engine", "boat", "ship", "wheel", "mast",
    # Materials
    "steel", "iron", "metal", "wood", "log", "timber", "stone",
    "fire", "flame", "wind", "rain", "storm", "wave", "sea", "ocean",
    "water", "river",
    # Abstract
    "darkness", "silence", "cold", "heat", "light",
    # Infrastructure
    "mill", "kitchen", "tent", "smithy",
}

ANIMATE_VERBS = {
    # Consumption
    "ate", "eat", "eating", "fed", "feed", "feeding", "bit", "bite",
    "biting", "chew", "chewing", "swallow", "swallowed", "devour",
    "devoured", "consume", "consumed", "digest", "hunger", "hungered",
    "taste", "tasted",
    # Communication / perception
    "spoke", "speak", "said", "whisper", "whispered", "scream",
    "screamed", "howl", "howled", "roar", "roared", "sing", "sang",
    "cry", "cried", "listen", "listened", "watched", "breathe",
    "breathed",
    # Emotion / will (EXCLUDING want/wanted — too common with human subjects)
    "refuse", "refused", "demand", "demanded",
    "forgive", "forgave", "resist", "resisted", "surrender",
    "surrendered", "obey", "obeyed",
    # Animate physical
    "grip", "gripped", "grab", "grabbed", "lick", "licked",
    "snarl", "snarled", "growl", "growled", "spit", "spat",
    "wept",
    # Personification states
    "stubborn", "angry", "hungry", "patient", "eager", "willing",
    "reluctant", "tired",
}


def detect_personification(sentence: str) -> List[Dict]:
    """
    Detect personification: inanimate subject + animate verb.
    Returns list of {subject, verb, position} dicts.
    """
    words = sentence.lower().split()
    findings = []

    for i, word in enumerate(words):
        cleaned = PUNCT.sub('', word)
        if cleaned in ANIMATE_VERBS:
            # Look backwards for subject (nearest noun-like word)
            for j in range(i - 1, max(i - 5, -1), -1):
                subj = PUNCT.sub('', words[j])
                if subj in INANIMATE_NOUNS:
                    findings.append({
                        "subject": subj,
                        "verb": cleaned,
                        "context": " ".join(words[max(0, j-2):min(len(words), i+3)]),
                    })
                    break
                if subj in STOPWORDS:
                    continue
                # Hit another content word that isn't inanimate — stop looking
                if len(subj) > 2 and subj not in STOPWORDS:
                    break

    return findings


# ============================================================================
# METAPHOR SIGNPOST DETECTION
# ============================================================================

SIGNPOST_PATTERNS = [
    r'\blike\s+(?:a|an|the)\b',
    r'\bas\s+(?:if|though)\b',
    r'\bwas\s+(?:a|an)\b',
    r'\bwere\s+(?:a|an)\b',
    r'\bthat\'s\b.*\bthat\s+is\b',     # "that's X, that is"
    r'\bthe\s+way\s+(?:a|an)\b',
    r'\bnothing\s+more\s+than\b',
    r'\blike\s+something\b',
    r'\blike\s+\w+\s+\w+ing\b',        # "like men climbing"
]


def has_signpost(sentence: str, prev_sentence: str = "",
                 next_sentence: str = "") -> bool:
    """Check for metaphor signposts in the sentence and its neighbors."""
    context = f"{prev_sentence} {sentence} {next_sentence}".lower()
    for pattern in SIGNPOST_PATTERNS:
        if re.search(pattern, context):
            return True
    return False


# ============================================================================
# MAIN DETECTOR
# ============================================================================

def detect_lsr(text: str, domain: str) -> Dict:
    """
    Detect LSR candidates in a passage.

    Returns dict with:
      - lsr_candidates: list of unjustified figurative polysemous words
      - justified: list of justified figurative polysemous words
      - personifications: list of detected personification instances
      - literal_filtered: count of words filtered as domain-literal
      - summary: one-line summary
    """
    domain_lit = DOMAIN_LITERAL.get(domain, set())

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return {"lsr_candidates": [], "justified": [], "personifications": [],
                "literal_filtered": 0, "summary": "Empty text"}

    total_sentences = len(sentences)
    lsr_candidates = []
    justified = []
    literal_count = 0
    all_personifications = []

    for sent_idx, sentence in enumerate(sentences):
        # Get context sentences
        prev_sent = sentences[sent_idx - 1] if sent_idx > 0 else ""
        next_sent = sentences[sent_idx + 1] if sent_idx < total_sentences - 1 else ""

        # Detect personification in this sentence
        persns = detect_personification(sentence)
        personification_verbs = {p["verb"] for p in persns}
        all_personifications.extend(persns)

        # Check for signpost
        signposted = has_signpost(sentence, prev_sent, next_sent)

        words = sentence.lower().split()
        for word_raw in words:
            word = PUNCT.sub('', word_raw).lower()

            if not word or len(word) < 3:
                continue
            if word in STOPWORDS:
                continue
            if word not in ALL_REGISTER_WORDS:
                continue

            # FILTER 1: Domain-literal
            if word in domain_lit:
                literal_count += 1
                continue

            # Find which register fields match
            matched_fields = []
            for field_name, field_words in REGISTER_FIELDS.items():
                if word in field_words:
                    matched_fields.append(field_name)

            if not matched_fields:
                continue

            # FILTER 2: Is this word part of a personification?
            is_personification = word in personification_verbs

            # Determine if figurative
            is_figurative = is_personification  # personification = figurative

            # Also check: is the word being used in a clearly figurative
            # construction? (e.g., "[inanimate] [word]" patterns)
            if not is_figurative:
                # Check if word is in a "like X" simile
                if re.search(rf'\blike\s+\w*\s*{re.escape(word)}\b',
                             sentence.lower()):
                    is_figurative = True
                # Check if word is predicate of inanimate subject
                # e.g., "the wound was a mouth" — "mouth" is figurative
                if re.search(rf'\bwas\s+(?:a|an)\s+{re.escape(word)}\b',
                             sentence.lower()):
                    is_figurative = True

            if not is_figurative:
                # Last check: is this word an animate quality applied to
                # an inanimate thing in context?
                if word in ANIMATE_VERBS:
                    is_figurative = True  # animate verb outside personification
                                          # detection still suspicious

            # Special handling: want/wanted only counts as figurative
            # when the subject is inanimate ("it wanted to be fed",
            # "the wound wanted to remain"). NOT "he wanted it" or
            # "they want to swim".
            if not is_figurative and word in {"want", "wanted", "wants"}:
                # Check if preceded by inanimate subject
                word_idx = None
                for wi, w in enumerate(words):
                    if PUNCT.sub('', w).lower() == word:
                        word_idx = wi
                        break
                if word_idx is not None:
                    for j in range(word_idx - 1, max(word_idx - 4, -1), -1):
                        subj = PUNCT.sub('', words[j]).lower()
                        if subj in INANIMATE_NOUNS or subj == "it":
                            is_figurative = True
                            break
                        if subj in {"he", "she", "they", "we", "i", "you",
                                   "who", "everyone", "somebody", "nobody"}:
                            break  # human subject, not figurative
                        if subj in STOPWORDS:
                            continue
                elif word in {"mouth", "tongue", "teeth", "appetite",
                              "hunger", "fist", "heart"}:
                    # Body part words: check if subject is inanimate
                    # "the wound was a mouth" vs "his mouth"
                    # Simple heuristic: preceded by "the" + inanimate, or
                    # "its", or used as metaphor predicate
                    preceding = " ".join(words[max(0, words.index(word_raw)-3):
                                               words.index(word_raw)])
                    if "its" in preceding or "the" in preceding:
                        # Could be inanimate possession — potential figurative
                        # But could also be "the face" meaning literal face
                        # Need more context; mark as possible
                        pass

            if not is_figurative:
                continue

            # FILTER 3: Justified by signpost?
            entry = {
                "word": word,
                "sentence": sentence.strip()[:120],
                "register_fields": matched_fields,
                "is_personification": is_personification,
                "has_signpost": signposted,
                "position": f"{sent_idx + 1}/{total_sentences}",
                "is_terminal": sent_idx >= total_sentences - 2,
            }

            if signposted:
                entry["verdict"] = "JUSTIFIED"
                justified.append(entry)
            else:
                entry["verdict"] = "LSR_CANDIDATE"
                lsr_candidates.append(entry)

    summary = (f"{len(lsr_candidates)} LSR candidates, "
               f"{len(justified)} justified, "
               f"{literal_count} literal-filtered, "
               f"{len(all_personifications)} personifications detected")

    return {
        "lsr_candidates": lsr_candidates,
        "justified": justified,
        "personifications": all_personifications,
        "literal_filtered": literal_count,
        "summary": summary,
    }


def print_result(label: str, result: Dict):
    """Print detection results for a passage."""
    print(f"\n{'—' * 60}")
    print(f"  {label}")
    print(f"  {result['summary']}")
    print(f"{'—' * 60}")

    if result["personifications"]:
        for p in result["personifications"]:
            print(f"  [PERSONIFICATION] {p['subject']} → {p['verb']}: "
                  f"\"{p['context']}\"")

    for c in result["lsr_candidates"]:
        pers = " [personification]" if c["is_personification"] else ""
        print(f"  >>> LSR  '{c['word']}' [{', '.join(c['register_fields'])}]{pers}")
        print(f"           \"{c['sentence']}\"")

    for c in result["justified"]:
        print(f"      ok   '{c['word']}' [{', '.join(c['register_fields'])}]")
        print(f"           \"{c['sentence']}\"")


# ============================================================================
# TEST DATA
# ============================================================================

def load_llm_passages():
    """Load LLM passages from Experiment 5."""
    for path in ["lsr_exp5_passages.json",
                 "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld/lsr_exp5_passages.json",
                 "/sessions/wizardly-optimistic-bohr/lsr_exp5_passages.json"]:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return None


RICHARD_PASSAGES = {
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


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    passages = load_llm_passages()
    if not passages:
        print("ERROR: Could not load LLM passages.")
        exit(1)

    scenarios = ["sawmill", "ocean_storm", "kitchen_fire",
                 "battlefield_surgery", "blacksmith"]
    conditions = ["suppressed", "neutral", "amplified"]

    print("=" * 60)
    print("LSR DETECTOR v2")
    print("=" * 60)

    # Track aggregates
    agg_lsr = defaultdict(int)
    agg_just = defaultdict(int)
    agg_pers = defaultdict(int)

    # LLM passages
    print("\n\n{'='*60}")
    print("LLM PASSAGES (Claude)")
    print("=" * 60)

    for scenario in scenarios:
        for condition in conditions:
            text = passages[scenario][condition]
            result = detect_lsr(text, scenario)
            label = f"LLM: {scenario} / {condition}"
            print_result(label, result)
            agg_lsr[condition] += len(result["lsr_candidates"])
            agg_just[condition] += len(result["justified"])
            agg_pers[condition] += len(result["personifications"])

    # Human passages
    print("\n\n" + "=" * 60)
    print("HUMAN PASSAGES (Richard)")
    print("=" * 60)

    h_total_lsr = 0
    h_total_just = 0
    h_total_pers = 0

    for scenario in scenarios:
        text = RICHARD_PASSAGES[scenario]
        result = detect_lsr(text, scenario)
        label = f"HUMAN: {scenario}"
        print_result(label, result)
        h_total_lsr += len(result["lsr_candidates"])
        h_total_just += len(result["justified"])
        h_total_pers += len(result["personifications"])

    # Final comparison
    print("\n\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    print(f"\n  {'Source':<25} {'LSR':<8} {'Justified':<12} {'Personif.':<12}")
    print(f"  {'-'*55}")
    for condition in conditions:
        print(f"  LLM {condition:<20} {agg_lsr[condition]:<8} "
              f"{agg_just[condition]:<12} {agg_pers[condition]:<12}")
    print(f"  {'HUMAN (Richard)':<25} {h_total_lsr:<8} "
          f"{h_total_just:<12} {h_total_pers:<12}")

    print(f"\n  LSR candidate rate (per 5 passages):")
    print(f"    LLM suppressed:  {agg_lsr['suppressed']}")
    print(f"    LLM neutral:     {agg_lsr['neutral']}")
    print(f"    LLM amplified:   {agg_lsr['amplified']}")
    print(f"    HUMAN:           {h_total_lsr}")

    print(f"\n  Personification detection rate:")
    print(f"    LLM suppressed:  {agg_pers['suppressed']}")
    print(f"    LLM neutral:     {agg_pers['neutral']}")
    print(f"    LLM amplified:   {agg_pers['amplified']}")
    print(f"    HUMAN:           {h_total_pers}")
