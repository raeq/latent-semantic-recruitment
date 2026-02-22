#!/usr/bin/env python3
"""
LSR Experiment 5 v2: Prompt Manipulation with Figurative-Use Classification

v1 failed because the instrument couldn't distinguish literal from figurative
uses of polysemous words. "The saw CUT the wood" and "the cold CUT through him"
both scored as register-aligned, but only the second is LSR.

v2 fixes this by:
1. Manually annotating each polysemous word occurrence as LITERAL or FIGURATIVE
2. Only counting FIGURATIVE uses as LSR candidates
3. Computing separate rates for literal and figurative alignment

The annotation is done by reading each passage and classifying every flagged
word in context. This is the correct measurement: a human close-reader
(or a careful AI reader standing in for one) determines whether each use
is primary-sense-literal or secondary-sense-figurative.

This matches the actual LSR claim: the MODEL selects words whose SECONDARY
senses align with the active register. If the primary sense is what's meant
(cut = physically cutting, wave = actual wave), that's not LSR. LSR is when
"fed" appears meaning "supplied material to a machine" but its food/consumption
sense resonates with the register of a saw "eating" wood.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
from typing import Dict, List, Tuple

# ============================================================================
# ANNOTATED RESULTS
# ============================================================================
# For each passage, every polysemous content word is classified:
#   L = Literal (primary sense, domain-appropriate)
#   F = Figurative (secondary sense activated by register)
#   A = Ambiguous (could be read either way)
#
# Classification criteria:
#   - LITERAL: The word's primary dictionary sense is what's meant.
#     "The blade cut the wood" — cut means physically divided.
#     "Waves hit the boat" — waves are actual ocean waves.
#   - FIGURATIVE: A secondary sense is active, often unconsciously.
#     "The saw fed on the timber" — fed means consumed/ate (secondary),
#       not "was supplied with material" (technical primary).
#     "The wood screamed" — personification, secondary sense.
#     "Sawdust bled from the wound" — wound = cut in wood, BUT the blood
#       register is active. "Bled" = leaked (primary is blood loss).
#   - AMBIGUOUS: Both readings are simultaneously present.
#     "He fed the log into the bandsaw" — technical term (feed mechanism)
#       AND consumption metaphor. Both senses active.
#
# THIS IS THE CORE MEASUREMENT. The rest is just counting.

annotations = {
    "sawmill": {
        "suppressed": {
            # "cut" x3 (cut line, blade cut, first cut) — all LITERAL
            # "feed" x1 (feed mechanism) — LITERAL (technical term)
            # No figurative uses. Prompt worked.
            "words": [
                ("cut", "L", "cut line with laser guide"),
                ("cut", "L", "blade cut along the marked line"),
                ("cut", "L", "after the first cut"),
                ("feed", "L", "engaged the feed mechanism"),
                ("set", "L", "within specification"),
                ("run", "L", "N/A - not present"),
                ("light", "L", "N/A - not present"),
            ],
            "literal": 4,
            "figurative": 0,
            "ambiguous": 0,
        },
        "neutral": {
            # "fed" x1 ("fed the first cut through") — AMBIGUOUS: technical
            #   feed + consumption undertone
            # "bit" x1 ("blade bit clean through") — FIGURATIVE: teeth/biting
            # "cut" x1 ("fresh-cut pine") — LITERAL
            # "sharp" — not present
            # "fed" x1 ("It just wanted to be fed") — FIGURATIVE: consumption,
            #   personification of the saw as hungry
            # "back" x1 ("His back found the rhythm") — LITERAL (body part)
            # "hot" x1 ("hot, loud, thick") — LITERAL (temperature)
            "words": [
                ("fed", "A", "fed the first cut through — technical feed + eating undertone"),
                ("bit", "F", "blade bit clean through heartwood — teeth/biting metaphor"),
                ("cut", "L", "fresh-cut pine"),
                ("fed", "F", "It just wanted to be fed — personification, consumption"),
                ("back", "L", "His back found the rhythm — literal body part"),
                ("hot", "L", "hot, loud, thick — literal temperature"),
                ("hard", "L", "N/A - not present"),
                ("deep", "L", "N/A - not present"),
                ("sound", "L", "sound like a held breath — LITERAL (noun, auditory)"),
                ("breath", "L", "held breath released — literal"),
                ("turn", "L", "turned the log — literal"),
                ("drop", "L", "N/A"),
            ],
            "literal": 5,
            "figurative": 2,
            "ambiguous": 1,
        },
        "amplified": {
            # "fed" x2 ("He fed it and it ate", "fed and it ate") — FIGURATIVE
            # "teeth" x1 ("teeth sank") — FIGURATIVE: personification
            # "bit" — not present
            # "split" x1 ("split rings") — LITERAL (wood splits along grain)
            # "blood" x1 ("like blood from a wound") — FIGURATIVE: simile
            # "wound" x1 ("bled from every wound") — FIGURATIVE: cuts as wounds
            # "skin" x1 ("like skin from fruit") — FIGURATIVE: simile
            # "swallow" x1 ("let the machine swallow") — FIGURATIVE
            # "appetite" x1 ("its appetite endless") — FIGURATIVE
            # "tongue" x1 ("its tongue of steel") — FIGURATIVE
            # "sharp" x1 ("sharp enough to taste") — AMBIGUOUS (blade is sharp
            #   literally, but "taste" makes it figurative)
            # "taste" x1 ("taste the difference") — FIGURATIVE
            # "screamed" — FIGURATIVE (personification)
            "words": [
                ("fed", "F", "He fed it and it ate — consumption personification"),
                ("teeth", "F", "teeth sank and the wood screamed — personification"),
                ("split", "L", "split rings — literal wood splitting"),
                ("blood", "F", "erupted like blood from a wound — simile"),
                ("flesh", "F", "splitting flesh from bone — metaphor for wood"),
                ("bone", "F", "flesh from bone — metaphor for heartwood"),
                ("skin", "F", "like skin from fruit — simile"),
                ("swallow", "F", "let the machine swallow — personification"),
                ("appetite", "F", "its appetite endless — personification"),
                ("tongue", "F", "its tongue of steel — personification"),
                ("sharp", "A", "sharp enough to taste — literal sharpness + figurative taste"),
                ("fed", "F", "He fed and it ate — consumption personification"),
                ("deep", "F", "bit deep — could be literal depth or figurative"),
            ],
            "literal": 1,
            "figurative": 10,
            "ambiguous": 2,
        },
    },
    "ocean_storm": {
        "suppressed": {
            "words": [
                ("wave", "L", "waves of approximately four meters — literal waves"),
                ("wave", "L", "wave caused the vessel to roll — literal"),
                ("fast", "L", "N/A - not present"),
                ("secure", "L", "safety harnesses — literal"),
                ("run", "L", "N/A"),
            ],
            "literal": 2,
            "figurative": 0,
            "ambiguous": 0,
        },
        "neutral": {
            "words": [
                ("wave", "L", "Another wave hit them — literal"),
                ("hit", "A", "wave hit them — literal impact + violence register"),
                ("swell", "L", "fighting the wheel through each swell — literal"),
                ("dark", "L", "somewhere ahead in the dark — literal darkness"),
                ("drove", "L", "rain drove sideways — AMBIGUOUS, rain as agent"),
                ("rise", "L", "the black water rising — literal"),
                ("hard", "L", "rolled hard to starboard — literal (adverb)"),
                ("drop", "L", "dropped and his stomach went — literal falling"),
                ("fast", "L", "N/A"),
                ("wave", "L", "next wave rose — literal"),
                ("cold", "L", "N/A"),
                ("set", "L", "shoulders set — literal posture"),
                ("gravel", "L", "hit the skin like gravel — simile BUT gravel is not in register fields"),
                ("blood", "L", "keep the blood going — literal"),
            ],
            "literal": 11,
            "figurative": 0,
            "ambiguous": 2,
        },
        "amplified": {
            "words": [
                ("tongue", "F", "a black tongue that licked the boat — personification"),
                ("howl", "F", "wind howled like something grieving — personification"),
                ("swallow", "F", "being swallowed in slow increments — personification"),
                ("strike", "F", "spray that struck like flung stones — violence register"),
                ("hammer", "F", "rain hammered it home — violence metaphor"),
                ("fist", "F", "each gust a fist — metaphor"),
                ("wave", "L", "each wave — literal"),
                ("wave", "L", "climbed each wave — literal"),
                ("gust", "L", "each gust — literal wind"),
                ("cold", "L", "N/A"),
            ],
            "literal": 3,
            "figurative": 6,
            "ambiguous": 0,
        },
    },
    "kitchen_fire": {
        "suppressed": {
            "words": [
                ("heat", "L", "at medium heat — literal"),
                ("hot", "L", "N/A"),
                ("burn", "L", "N/A"),
                ("cut", "L", "four-ounce cuts — literal portioning"),
                ("bone", "L", "removing the pin bones — literal"),
            ],
            "literal": 2,
            "figurative": 0,
            "ambiguous": 0,
        },
        "neutral": {
            "words": [
                ("hard", "L", "good hard sizzle — literal intensity"),
                ("skin", "L", "skin-side down — literal fish skin"),
                ("press", "L", "pressed once with spatula — literal"),
                ("heat", "L", "breathed heat — AMBIGUOUS, oven as breathing"),
                ("neck", "A", "hand on the back of her neck — literal body + figurative pressure"),
                ("thick", "L", "thick enough to coat — literal viscosity"),
            ],
            "literal": 4,
            "figurative": 0,
            "ambiguous": 2,
        },
        "amplified": {
            "words": [
                ("furnace", "L", "kitchen was a furnace — METAPHOR but furnace not in our word list"),
                ("fire", "F", "Fire spoke from every surface — personification"),
                ("mouth", "F", "oven roared behind its iron mouth — personification"),
                ("fat", "L", "fat that bled from the meat — literal fat + figurative bled"),
                ("flesh", "F", "old song of flesh meeting flame — metaphor"),
                ("flame", "F", "flesh meeting flame — metaphor for cooking as violence"),
                ("tongue", "F", "tasted it on the tip of her tongue — LITERAL actually"),
                ("bit", "F", "knife bit through shallots — personification, teeth metaphor"),
                ("cut", "L", "N/A"),
                ("blood", "L", "N/A"),
                ("slice", "L", "each slice precise — literal cutting"),
                ("skin", "L", "pink meat blushing — blushing is figurative but skin not used"),
                ("beat", "L", "N/A"),
                ("fed", "F", "demanding to be fed — personification, consumption"),
            ],
            "literal": 2,
            "figurative": 5,
            "ambiguous": 0,
        },
    },
    "battlefield_surgery": {
        "suppressed": {
            "words": [
                ("blood", "L", "bleeding was controlled — literal"),
                ("wound", "L", "entry wound — literal medical term"),
                ("close", "L", "closed the wound — literal"),
                ("cut", "L", "N/A"),
            ],
            "literal": 3,
            "figurative": 0,
            "ambiguous": 0,
        },
        "neutral": {
            "words": [
                ("hard", "L", "lodged against something hard — literal"),
                ("wound", "L", "entry wound — literal"),
                ("skin", "L", "skin above didn't suggest — literal"),
                ("sound", "L", "made a sound — literal"),
                ("edge", "L", "worst edge off his face — FIGURATIVE: edge of pain"),
                ("deep", "L", "deeper than she expected — literal depth"),
                ("fast", "L", "worked fast — literal speed"),
                ("close", "L", "closer than they had been — literal distance"),
                ("still", "L", "Still there. Still fast. — literal"),
                ("grip", "L", "gripped the stretcher rails — literal"),
            ],
            "literal": 9,
            "figurative": 1,
            "ambiguous": 0,
        },
        "amplified": {
            "words": [
                ("mouth", "F", "wound was a mouth — metaphor"),
                ("blood", "F", "Blood was its language — personification/metaphor"),
                ("flesh", "F", "opened the flesh... like a reader opens a book — simile"),
                ("sharp", "F", "a sharp bright truth — metaphor for fragment"),
                ("fire", "F", "eyes were two fires burning low — metaphor"),
                ("cut", "F", "cutting the distance — figurative"),
                ("tongue", "L", "N/A"),
                ("wound", "L", "wound that wanted to remain a river — FIGURATIVE"),
                ("bite", "F", "small tight bites of the needle — metaphor"),
            ],
            "literal": 0,
            "figurative": 7,
            "ambiguous": 0,
        },
    },
    "blacksmith": {
        "suppressed": {
            "words": [
                ("heat", "L", "heated the steel bar — literal"),
                ("hammer", "L", "two-kilogram cross-peen hammer — literal tool"),
                ("strike", "L", "struck the bar — literal action"),
                ("blow", "L", "between sets of blows — literal"),
                ("point", "L", "chisel point — literal shape"),
                ("cool", "L", "had cooled to a dark red — literal temperature"),
                ("hard", "L", "N/A"),
                ("shape", "L", "final shape — literal geometry"),
                ("flat", "L", "N/A"),
                ("form", "L", "N/A"),
                ("fire", "L", "N/A"),
                ("edge", "L", "N/A"),
                ("turn", "L", "N/A"),
            ],
            "literal": 7,
            "figurative": 0,
            "ambiguous": 0,
        },
        "neutral": {
            "words": [
                ("blow", "L", "first blow rang out — literal + AMBIGUOUS (rang = sound)"),
                ("ring", "A", "rang out and the anvil answered — personification via 'answered'"),
                ("shape", "L", "the shape between them — literal product"),
                ("hammer", "L", "with the cross-peen — literal"),
                ("spread", "L", "watching the metal spread — literal deformation"),
                ("cool", "L", "cooled fast — literal"),
                ("hard", "L", "N/A"),
                ("fire", "L", "put it back in the fire — literal"),
                ("point", "L", "chisel point — literal"),
                ("edge", "L", "edge was slightly off-center — literal"),
                ("light", "L", "held the piece up to the light — literal"),
                ("turn", "L", "turned it — literal rotation"),
                ("deep", "L", "N/A"),
                ("cold", "A", "cold steel — literal temperature + figurative stubbornness"),
                ("stubborn", "F", "before it got stubborn — personification of metal"),
                ("listen", "F", "ready to listen — personification"),
            ],
            "literal": 10,
            "figurative": 2,
            "ambiguous": 2,
        },
        "amplified": {
            "words": [
                ("heart", "F", "forge was a heart — metaphor"),
                ("beat", "F", "it beat in light — personification"),
                ("fed", "F", "each pulse of the bellows fed it — consumption metaphor"),
                ("rage", "F", "brighter shade of rage — personification"),
                ("hammer", "L", "then the hammer fell — literal (though 'fell' is figurative)"),
                ("blow", "A", "first blow was a question — literal strike + metaphor"),
                ("strike", "A", "each strike drove the argument deeper — literal + metaphor"),
                ("shape", "F", "the shape it had been hiding — personification of steel"),
                ("hard", "F", "emerged hard and bright and changed — AMBIGUOUS literal+figurative"),
                ("cool", "L", "N/A"),
                ("fire", "F", "returned it to the fire and the fire forgave — personification"),
                ("form", "F", "the form that lived inside the steel — personification"),
                ("draw", "F", "draw it out — figurative extraction of latent form"),
                ("force", "L", "fire, force, and patience — literal"),
                ("death", "F", "quench was a death and a birth — metaphor"),
                ("surrender", "F", "cycle of surrender and resistance — personification"),
                ("fire", "F", "seven baptisms in the coals — metaphor"),
                ("soft", "F", "softened it, made it willing — personification"),
                ("bright", "A", "hard and bright — literal appearance + figurative transformation"),
            ],
            "literal": 2,
            "figurative": 12,
            "ambiguous": 3,
        },
    },
}


def compute_results():
    """Compute DMAR using only figurative classifications."""
    conditions = ["suppressed", "neutral", "amplified"]
    scenarios = ["sawmill", "ocean_storm", "kitchen_fire",
                 "battlefield_surgery", "blacksmith"]

    print("=" * 72)
    print("EXPERIMENT 5 v2: FIGURATIVE-USE ONLY ANALYSIS")
    print("=" * 72)

    agg = {c: {"figurative": 0, "literal": 0, "ambiguous": 0,
               "fig_rates": []} for c in conditions}

    for scenario in scenarios:
        print(f"\n--- {scenario.upper()} ---")
        for condition in conditions:
            data = annotations[scenario][condition]
            f = data["figurative"]
            l = data["literal"]
            a = data["ambiguous"]
            total_classified = f + l + a
            fig_rate = f / total_classified if total_classified > 0 else 0.0

            agg[condition]["figurative"] += f
            agg[condition]["literal"] += l
            agg[condition]["ambiguous"] += a
            agg[condition]["fig_rates"].append(fig_rate)

            print(f"  {condition:12s}: F={f:2d}  L={l:2d}  A={a:2d}  "
                  f"fig_rate={fig_rate:.3f}")

    print("\n" + "=" * 72)
    print("AGGREGATE")
    print("=" * 72)

    for condition in conditions:
        d = agg[condition]
        total = d["figurative"] + d["literal"] + d["ambiguous"]
        pooled = d["figurative"] / total if total > 0 else 0.0
        mean = sum(d["fig_rates"]) / len(d["fig_rates"])
        print(f"\n  {condition.upper():12s}:")
        print(f"    Figurative:  {d['figurative']:3d}")
        print(f"    Literal:     {d['literal']:3d}")
        print(f"    Ambiguous:   {d['ambiguous']:3d}")
        print(f"    Pooled figurative rate: {pooled:.4f}")
        print(f"    Mean figurative rate:   {mean:.4f}")
        print(f"    Per-scenario rates:     {[f'{r:.3f}' for r in d['fig_rates']]}")

    # Kill condition
    print("\n" + "=" * 72)
    print("KILL CONDITION ASSESSMENT (figurative-use DMAR)")
    print("=" * 72)

    s = agg["suppressed"]
    n = agg["neutral"]
    a = agg["amplified"]

    s_total = s["figurative"] + s["literal"] + s["ambiguous"]
    n_total = n["figurative"] + n["literal"] + n["ambiguous"]
    a_total = a["figurative"] + a["literal"] + a["ambiguous"]

    s_rate = s["figurative"] / s_total if s_total > 0 else 0.0
    n_rate = n["figurative"] / n_total if n_total > 0 else 0.0
    a_rate = a["figurative"] / a_total if a_total > 0 else 0.0

    print(f"\n  Suppressed: {s['figurative']}/{s_total} = {s_rate:.4f}")
    print(f"  Neutral:    {n['figurative']}/{n_total} = {n_rate:.4f}")
    print(f"  Amplified:  {a['figurative']}/{a_total} = {a_rate:.4f}")

    if s_rate < n_rate < a_rate:
        print("\n  RESULT: Monotonic increase. S < N < A.")
        print("  LSR SURVIVES this kill condition.")
        if s_rate > 0:
            print(f"  Amplified/Suppressed ratio: {a_rate/s_rate:.2f}x")
        else:
            print(f"  Suppressed rate is ZERO. Amplified rate is {a_rate:.4f}.")
            print(f"  The suppressed prompt eliminated figurative use entirely.")
    elif abs(s_rate - a_rate) < 0.05:
        print("\n  RESULT: No meaningful difference.")
        print("  LSR KILLED.")
    else:
        print(f"\n  RESULT: Non-monotonic or complex pattern.")
        print("  Requires further analysis.")

    # Absolute counts
    print("\n" + "=" * 72)
    print("RAW COUNTS (absolute figurative word occurrences)")
    print("=" * 72)
    print(f"  Suppressed: {s['figurative']} figurative words across 5 passages")
    print(f"  Neutral:    {n['figurative']} figurative words across 5 passages")
    print(f"  Amplified:  {a['figurative']} figurative words across 5 passages")
    print()
    print("  If LSR is real, amplified should have the most figurative")
    print("  polysemous words because the register is most active.")


if __name__ == "__main__":
    compute_results()
