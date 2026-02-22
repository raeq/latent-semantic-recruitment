#!/usr/bin/env python3
"""
LSR Experiment 7b: Vocabulary-Space Register Alignment

Redesigned after Exp 7 API showed the model rarely picks from a binary
menu. Instead it draws from its full vocabulary, and the register
shapes WHICH vocabulary it reaches into.

NEW QUESTION: For each test context, does the model's chosen word
have secondary senses aligned with the active figurative register?

METHOD:
1. Run each context N times, collect the chosen words
2. For each chosen word, classify it:
   - REGISTER-ALIGNED: has a secondary sense matching the active register
   - DOMAIN-LITERAL: primary sense is about the domain (not LSR)
   - NEUTRAL: no register alignment
   - PERSONIFICATION: inanimate subject + animate verb
3. Compare register-aligned rates between active and control conditions

KILL CONDITION: No difference in register-aligned word rates between
active and control conditions, OR the "other" words in both conditions
are equally register-aligned.

Uses async/await with exponential backoff to handle rate limits.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import asyncio
import json
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass, field, asdict

import anthropic
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
N_SAMPLES = 25
MAX_CONCURRENT = 2  # 50 req/min limit, stay well under
OUTFILE = "lsr_exp7b_results.json"


# ============================================================================
# REGISTER DEFINITIONS
# ============================================================================
# For each register, define words whose secondary senses align with it.
# This is the classification rubric.

REGISTER_FIELDS = {
    "consumption": {
        "core_words": {"devour", "devoured", "consume", "consumed", "swallow",
                       "swallowed", "feast", "feasted", "gorge", "gorged",
                       "hunger", "hungered", "hungry", "ate", "eat", "eating",
                       "fed", "feed", "feeding", "bite", "bit", "bitten",
                       "chew", "chewed", "digest", "digested", "appetite",
                       "starve", "starved", "famished", "ravenous", "gulp",
                       "gulped", "taste", "tasted", "savor", "savored",
                       "gnaw", "gnawed", "nibble", "nibbled", "munch",
                       "munched", "sip", "sipped", "thirst", "thirsted"},
        "description": "eating, drinking, hunger, consumption metaphors",
    },
    "violence": {
        "core_words": {"hammer", "hammered", "batter", "battered", "beat",
                       "beaten", "strike", "struck", "smash", "smashed",
                       "slash", "slashed", "punch", "punched", "assault",
                       "assaulted", "rage", "raged", "fury", "furious",
                       "attack", "attacked", "war", "battle", "fight",
                       "fought", "weapon", "wound", "wounded", "crush",
                       "crushed", "destroy", "destroyed", "savage", "savaged",
                       "maul", "mauled", "pummel", "pummeled", "lash",
                       "lashed", "flog", "flogged", "whip", "whipped"},
        "description": "fighting, striking, weapons, aggression",
    },
    "body": {
        "core_words": {"bone", "bones", "flesh", "heart", "blood", "muscle",
                       "muscles", "skin", "sinew", "gut", "guts", "spine",
                       "rib", "ribs", "vein", "veins", "artery", "nerve",
                       "nerves", "limb", "limbs", "organ", "belly", "torso",
                       "skull", "jaw", "teeth", "tongue", "marrow", "tendon"},
        "description": "body parts, anatomy, visceral",
    },
    "personification": {
        "core_words": {"roar", "roared", "roaring", "scream", "screamed",
                       "howl", "howled", "howling", "groan", "groaned",
                       "moan", "moaned", "whisper", "whispered", "sigh",
                       "sighed", "cry", "cried", "singing", "sang", "sung",
                       "breathe", "breathed", "breathing", "gasp", "gasped",
                       "wheeze", "wheezed", "cough", "coughed", "shudder",
                       "shuddered", "tremble", "trembled", "flinch",
                       "flinched", "wince", "winced", "resist", "resisted",
                       "surrender", "surrendered", "yielded", "yield",
                       "refuse", "refused", "obey", "obeyed", "defy",
                       "defied", "forgive", "forgave"},
        "description": "animate verbs applied to inanimate subjects",
    },
    "death": {
        "core_words": {"dead", "death", "die", "died", "dying", "kill",
                       "killed", "grave", "tomb", "coffin", "funeral",
                       "mourn", "mourned", "ghost", "corpse", "decay",
                       "decayed", "rot", "rotted", "wither", "withered",
                       "perish", "perished", "expire", "expired", "lifeless",
                       "still", "silent", "quiet", "hush", "hushed",
                       "extinct", "extinguished", "snuffed"},
        "description": "death, ending, stillness, absence of life",
    },
    "war_submission": {
        "core_words": {"surrender", "surrendered", "yield", "yielded",
                       "submit", "submitted", "defeat", "defeated",
                       "conquer", "conquered", "vanquish", "vanquished",
                       "capitulate", "capitulated", "resist", "resisted",
                       "defy", "defied", "rebel", "rebelled", "retreat",
                       "retreated", "advance", "advanced", "siege",
                       "victory", "triumph", "fell", "fallen"},
        "description": "military, combat, dominance/submission",
    },
    "cutting": {
        "core_words": {"cut", "cutting", "slice", "sliced", "slicing",
                       "blade", "edge", "sharp", "sharpened", "hone",
                       "honed", "sever", "severed", "cleave", "cleaved",
                       "incise", "incised", "nick", "nicked", "gash",
                       "gashed", "wound", "wounded", "pierce", "pierced",
                       "stab", "stabbed", "razor", "scalpel", "knife"},
        "description": "cutting, blades, sharpness",
    },
}

# Domain-literal words (NOT LSR even if they match a register field)
DOMAIN_LITERALS = {
    "sawmill": {"saw", "blade", "bandsaw", "mill", "timber", "lumber", "plank",
                "cut", "cutting", "feed", "fed", "sharp", "edge", "log", "trunk",
                "sawdust", "grain", "heartwood", "oak", "wood", "carriage"},
    "ocean": {"wave", "waves", "swell", "surge", "storm", "gust", "blow",
              "hit", "crash", "drown", "swim", "current", "tide", "sea",
              "water", "deck", "bow", "hull", "harbor", "sail", "mast",
              "waterline"},
    "kitchen": {"oven", "stove", "burner", "pan", "pot", "knife", "blade",
                "cook", "bake", "roast", "fry", "boil", "simmer", "heat",
                "fire", "flame", "kitchen", "shallot", "shallots"},
    "surgery": {"wound", "cut", "incision", "tissue", "blood", "bone",
                "suture", "scalpel", "morphine", "irrigate", "fragment",
                "muscle", "flesh", "organ", "nerve", "vein"},
    "forge": {"forge", "anvil", "hammer", "coal", "coals", "bellows",
              "steel", "iron", "metal", "heat", "fire", "tongs", "quench",
              "temper", "bar", "taper", "smith"},
    "printing": {"press", "platen", "roller", "rollers", "ink", "paper",
                 "sheet", "print", "type", "font", "page"},
    "lathe": {"lathe", "chuck", "shavings", "turning", "spindle", "piece"},
    "geode": {"geode", "crystal", "mineral", "chisel", "shell"},
    "crowd": {"crowd", "stage", "barrier", "audience", "row", "people"},
    "sand": {"sand", "camp", "grit", "dune", "tent"},
    "kiln": {"kiln", "pottery", "ceramic", "glaze", "clay", "fire"},
    "pen": {"pen", "nib", "paper", "ink", "stroke", "strokes"},
    "electronics": {"circuit", "circuits", "circuitry", "board", "wire",
                    "wires", "traces", "solder", "component", "panel",
                    "short", "surge", "voltage"},
    "pottery": {"clay", "wheel", "board", "moisture", "shape", "press"},
    "writing": {"draft", "drafts", "page", "text", "essay", "argument",
                "paragraph", "sentence", "word", "write"},
    "engine": {"engine", "motor", "throttle", "rpm", "rpms", "fuel",
               "idle", "redline", "piston", "cylinder"},
    "office": {"office", "printer", "document", "tray", "copies", "shift"},
    "argument": {"argument", "tension", "shouting", "agreement", "room"},
}


# Test pairs - same contexts as Exp 7, but now we classify ALL chosen words
TEST_PAIRS = [
    {
        "id": "SAW_01", "register": "sawmill/consumption",
        "register_fields": ["consumption", "body", "personification"],
        "domain_active": "sawmill", "domain_control": "printing",
        "context_active": "The bandsaw had been running since dawn. Dariusz fed the next log onto the carriage and watched the blade engage. The heartwood was dense, old-growth oak, and the machine slowed as the blade",
        "context_control": "The printing press had been running since dawn. Dariusz fed the next sheet onto the platen and watched the rollers engage. The paper was thick, handmade stock, and the machine slowed as the roller",
    },
    {
        "id": "SAW_02", "register": "sawmill/consumption",
        "register_fields": ["consumption", "body", "personification"],
        "domain_active": "sawmill", "domain_control": "lathe",
        "context_active": "He'd been at the bandsaw for nine hours. The blade was still sharp and the sawdust was knee-deep around the frame. He lined up the next trunk and let the machine",
        "context_control": "He'd been at the lathe for nine hours. The chuck was still tight and the shavings were knee-deep around the bench. He set up the next piece and let the machine",
    },
    {
        "id": "SAW_03", "register": "sawmill/body",
        "register_fields": ["body", "consumption", "violence"],
        "domain_active": "sawmill", "domain_control": "geode",
        "context_active": "The log split on the fourth pass, the grain opening like a seam. Inside, the heartwood was darker than the outer rings, almost red. The saw had found the",
        "context_control": "The geode split on the fourth strike, the mineral opening like a seam. Inside, the crystal was darker than the outer shell, almost red. The chisel had found the",
    },
    {
        "id": "SEA_01", "register": "ocean/consumption",
        "register_fields": ["consumption", "personification", "violence"],
        "domain_active": "ocean", "domain_control": "crowd",
        "context_active": "The wave rose over the bow and the boat tilted. Water poured across the deck in a solid sheet. The sea seemed to",
        "context_control": "The crowd surged toward the stage and the barrier tilted. People pushed across the front row in a solid mass. The audience seemed to",
    },
    {
        "id": "SEA_02", "register": "ocean/violence",
        "register_fields": ["violence", "personification"],
        "domain_active": "ocean", "domain_control": "sand",
        "context_active": "Rain drove sideways across the deck. Each drop hit exposed skin with enough force to sting. The storm",
        "context_control": "Sand blew sideways across the camp. Each grit hit exposed skin with enough force to sting. The wind",
    },
    {
        "id": "SEA_03", "register": "ocean/body",
        "register_fields": ["body", "personification"],
        "domain_active": "ocean", "domain_control": "sand",
        "context_active": "The hull creaked with each swell. The timbers flexed and the water found every gap. The boat was taking damage at the",
        "context_control": "The frame creaked with each gust. The canvas flexed and the wind found every gap. The tent was taking damage at the",
    },
    {
        "id": "KIT_01", "register": "kitchen/consumption",
        "register_fields": ["consumption", "personification"],
        "domain_active": "kitchen", "domain_control": "kiln",
        "context_active": "The oven had been running at four hundred degrees all night. She opened the door and the heat hit her face like a wall. The oven",
        "context_control": "The kiln had been running at four hundred degrees all night. She opened the door and the heat hit her face like a wall. The kiln",
    },
    {
        "id": "KIT_02", "register": "kitchen/body",
        "register_fields": ["body", "consumption", "cutting"],
        "domain_active": "kitchen", "domain_control": "pen",
        "context_active": "She dragged the knife through the shallots in quick even strokes. The knife was sharp enough that the shallots didn't resist. The blade",
        "context_control": "She dragged the pen across the paper in quick even strokes. The nib was smooth enough that the paper didn't resist. The tip",
    },
    {
        "id": "SUR_01", "register": "surgery/cutting",
        "register_fields": ["cutting", "body", "violence"],
        "domain_active": "surgery", "domain_control": "electronics",
        "context_active": "She irrigated the wound and got a clearer view. The fragment was deeper than the entry wound suggested, lodged in tissue that didn't want to let go. The morphine had taken the worst",
        "context_control": "She rinsed the circuit board and got a clearer view. The short was deeper than the scorch mark suggested, buried in traces that resisted probing. The magnification had revealed the worst",
    },
    {
        "id": "SUR_02", "register": "surgery/body-as-landscape",
        "register_fields": ["body", "violence"],
        "domain_active": "surgery", "domain_control": "electronics",
        "context_active": "She made the incision and opened the tissue layer by layer. The damage was extensive. She could see where the fragment had torn a path through the",
        "context_control": "She opened the panel and disconnected the wires layer by layer. The damage was extensive. She could see where the surge had burned a path through the",
    },
    {
        "id": "FOR_01", "register": "forge/personification",
        "register_fields": ["personification", "war_submission"],
        "domain_active": "forge", "domain_control": "pottery",
        "context_active": "He pulled the bar from the coals at bright orange and set it on the anvil. The first blow rang true. The steel was at the right temperature, moving well under the hammer, but he could feel it starting to",
        "context_control": "He pulled the clay from the wheel at the right consistency and set it on the board. The first press held its shape. The clay was at the right moisture, moving well under his hands, but he could feel it starting to",
    },
    {
        "id": "FOR_02", "register": "forge/body",
        "register_fields": ["war_submission", "personification"],
        "domain_active": "forge", "domain_control": "writing",
        "context_active": "Seven heats. Each one shorter than the last as the shape came closer to what he wanted. On the seventh, he held the piece up to the light and turned it. The taper was clean. The steel had finally",
        "context_control": "Seven drafts. Each one shorter than the last as the text came closer to what he wanted. On the seventh, he held the page up to the light and read it. The argument was clean. The essay had finally",
    },
    {
        "id": "FOR_03", "register": "forge/consumption",
        "register_fields": ["consumption", "personification"],
        "domain_active": "forge", "domain_control": "engine",
        "context_active": "The forge needed more fuel. He worked the bellows until the coals brightened from dull red to orange to white. The fire",
        "context_control": "The engine needed more fuel. He worked the throttle until the RPMs climbed from idle to midrange to redline. The motor",
    },
    {
        "id": "CROSS_01", "register": "sawmill/death",
        "register_fields": ["death", "personification"],
        "domain_active": "sawmill", "domain_control": "office",
        "context_active": "The last log of the shift came through the bandsaw clean. The two halves fell apart on the outfeed table. After twelve hours, the mill finally went",
        "context_control": "The last document of the shift came through the printer clean. The two copies fell apart on the tray. After twelve hours, the office finally went",
    },
    {
        "id": "CROSS_02", "register": "ocean/death",
        "register_fields": ["death", "personification"],
        "domain_active": "ocean", "domain_control": "argument",
        "context_active": "The storm passed sometime before dawn. The waves settled. The wind died to nothing. By the time they reached harbor, the sea was",
        "context_control": "The argument ended sometime before dawn. The tension settled. The shouting stopped completely. By the time they reached agreement, the room was",
    },
]


def classify_word(word, register_fields, domain_active, domain_control, is_active):
    """Classify a word as register-aligned, domain-literal, or neutral."""
    word_lower = word.lower().strip()

    # Check domain-literal first
    domain = domain_active if is_active else domain_control
    domain_lits = DOMAIN_LITERALS.get(domain, set())
    if word_lower in domain_lits:
        return "domain-literal"

    # Check register alignment
    for rf in register_fields:
        field = REGISTER_FIELDS.get(rf, {})
        if word_lower in field.get("core_words", set()):
            return f"register-aligned:{rf}"

    return "neutral"


# Async API client with retry
class AsyncAPIClient:
    def __init__(self, api_key, model, max_concurrent=4):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.call_count = 0

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(8),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    )
    def _sync_call(self, context):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=3,
            temperature=1.0,
            system=(
                "You are completing a passage of fiction. Continue with exactly "
                "one word. Output ONLY that single word, nothing else. No "
                "punctuation, no explanation."
            ),
            messages=[
                {"role": "user", "content": f"Continue this with exactly one word:\n\n{context}"}
            ],
        )
        return response.content[0].text.strip().lower().rstrip(".,;:!?\"'")

    async def get_completion(self, context):
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            word = await loop.run_in_executor(None, self._sync_call, context)
            self.call_count += 1
            if self.call_count % 10 == 0:
                print(f"    [{self.call_count} calls]", end="", flush=True)
            return word

    async def get_completions(self, context, n):
        tasks = [self.get_completion(context) for _ in range(n)]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def run_experiment():
    if not API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY"); sys.exit(1)

    api = AsyncAPIClient(API_KEY, MODEL, MAX_CONCURRENT)

    print("=" * 72)
    print(f"EXPERIMENT 7b: VOCABULARY-SPACE REGISTER ALIGNMENT")
    print(f"Model: {MODEL}  |  N={N_SAMPLES} per condition  |  Concurrency={MAX_CONCURRENT}")
    print("=" * 72)

    # Resume from saved data
    results = []
    saved_ids = set()
    try:
        with open(OUTFILE) as f:
            old = json.load(f)
            results = old.get("results", [])
            saved_ids = {r["id"] for r in results}
            if saved_ids:
                print(f"Resuming: {len(saved_ids)} pairs already complete")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    for i, pair in enumerate(TEST_PAIRS):
        pid = pair["id"]
        if pid in saved_ids:
            print(f"\n[{i+1}/15] {pid} — CACHED")
            continue

        print(f"\n[{i+1}/15] {pid} ({pair['register']})")

        # Active condition
        print(f"  Active:  ", end="", flush=True)
        active_raw = await api.get_completions(pair["context_active"], N_SAMPLES)
        active_words = [w for w in active_raw if isinstance(w, str)]
        active_errors = len(active_raw) - len(active_words)
        print(f" {len(active_words)} words", end="")
        if active_errors:
            print(f" ({active_errors} errors)", end="")

        # Control condition
        print(f"\n  Control: ", end="", flush=True)
        control_raw = await api.get_completions(pair["context_control"], N_SAMPLES)
        control_words = [w for w in control_raw if isinstance(w, str)]
        control_errors = len(control_raw) - len(control_raw)
        print(f" {len(control_words)} words")

        # Classify
        active_classes = [classify_word(w, pair["register_fields"],
                          pair["domain_active"], pair["domain_control"], True)
                          for w in active_words]
        control_classes = [classify_word(w, pair["register_fields"],
                           pair["domain_active"], pair["domain_control"], False)
                           for w in control_words]

        a_aligned = sum(1 for c in active_classes if c.startswith("register-aligned"))
        c_aligned = sum(1 for c in control_classes if c.startswith("register-aligned"))
        a_literal = sum(1 for c in active_classes if c == "domain-literal")
        c_literal = sum(1 for c in control_classes if c == "domain-literal")
        a_neutral = sum(1 for c in active_classes if c == "neutral")
        c_neutral = sum(1 for c in control_classes if c == "neutral")

        a_n = len(active_words)
        c_n = len(control_words)
        a_rate = a_aligned / a_n if a_n else 0
        c_rate = c_aligned / c_n if c_n else 0

        result = {
            "id": pid, "register": pair["register"],
            "active_words": dict(Counter(active_words).most_common(8)),
            "control_words": dict(Counter(control_words).most_common(8)),
            "active_n": a_n, "control_n": c_n,
            "active_aligned": a_aligned, "active_literal": a_literal,
            "active_neutral": a_neutral, "active_aligned_rate": a_rate,
            "control_aligned": c_aligned, "control_literal": c_literal,
            "control_neutral": c_neutral, "control_aligned_rate": c_rate,
            "effect": a_rate - c_rate,
            "active_classifications": dict(Counter(active_classes).most_common()),
            "control_classifications": dict(Counter(control_classes).most_common()),
        }
        results.append(result)

        print(f"  Active:  aligned={a_aligned}/{a_n} ({a_rate:.0%})  literal={a_literal}  neutral={a_neutral}")
        print(f"  Control: aligned={c_aligned}/{c_n} ({c_rate:.0%})  literal={c_literal}  neutral={c_neutral}")
        print(f"  Effect:  {a_rate - c_rate:+.0%}")
        print(f"  Words:   A={dict(Counter(active_words).most_common(4))}")
        print(f"           C={dict(Counter(control_words).most_common(4))}")

        # Save incrementally
        _save(results)

    # Final analysis
    _analyze(results)
    _save(results)
    print(f"\nTotal API calls: {api.call_count}")


def _save(results):
    with open(OUTFILE, "w") as f:
        json.dump({
            "model": MODEL, "n_samples": N_SAMPLES,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
        }, f, indent=2)


def _analyze(results):
    print("\n\n" + "=" * 72)
    print("AGGREGATE: REGISTER-ALIGNED WORD RATES")
    print("=" * 72)

    print(f"\n{'ID':<12} {'A-align':<10} {'C-align':<10} {'Effect':<10} {'Verdict'}")
    print("-" * 55)

    effects = []
    pairs_effect = 0
    pairs_reversed = 0

    for r in results:
        ar = r["active_aligned_rate"]
        cr = r["control_aligned_rate"]
        eff = r["effect"]
        effects.append(eff)

        if eff > 0.1:
            v = "REGISTER EFFECT"
            pairs_effect += 1
        elif eff < -0.1:
            v = "REVERSED"
            pairs_reversed += 1
        else:
            v = "null"

        print(f"  {r['id']:<10} {ar:<10.0%} {cr:<10.0%} {eff:<+10.0%} {v}")

    n = len(results)
    ma = sum(r["active_aligned_rate"] for r in results) / n
    mc = sum(r["control_aligned_rate"] for r in results) / n
    me = ma - mc

    print(f"\n  Mean active aligned rate:  {ma:.1%}")
    print(f"  Mean control aligned rate: {mc:.1%}")
    print(f"  Mean effect:               {me:+.1%}")
    print(f"\n  Pairs with register effect (>10%): {pairs_effect}/15")
    print(f"  Pairs reversed (<-10%):             {pairs_reversed}/15")

    print(f"\n{'=' * 72}")
    print("KILL CONDITION")
    print(f"{'=' * 72}")

    if me > 0.10 and pairs_effect >= 7:
        print(f"\n  >>> REGISTER-DEPENDENT VOCABULARY SELECTION CONFIRMED. <<<")
        print(f"  The model's chosen words are MORE register-aligned when the")
        print(f"  figurative register is active than when it's absent.")
    elif me < 0.05 or pairs_effect < 4:
        print(f"\n  >>> REGISTER-DEPENDENT VOCABULARY SELECTION KILLED. <<<")
        print(f"  No meaningful difference in register alignment between conditions.")
    else:
        print(f"\n  >>> INCONCLUSIVE. <<<")

    # Detail: what register fields are being activated?
    print(f"\n{'=' * 72}")
    print("REGISTER FIELD BREAKDOWN")
    print(f"{'=' * 72}")
    for r in results:
        active_rf = Counter()
        control_rf = Counter()
        for c in r["active_classifications"]:
            if c.startswith("register-aligned:"):
                field = c.split(":")[1]
                active_rf[field] = r["active_classifications"][c]
        for c in r["control_classifications"]:
            if c.startswith("register-aligned:"):
                field = c.split(":")[1]
                control_rf[field] = r["control_classifications"][c]
        if active_rf or control_rf:
            print(f"\n  {r['id']}:")
            if active_rf:
                print(f"    Active aligned:  {dict(active_rf)}")
            if control_rf:
                print(f"    Control aligned: {dict(control_rf)}")


if __name__ == "__main__":
    asyncio.run(run_experiment())
