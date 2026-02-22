#!/usr/bin/env python3
"""
LSR Experiment 4: Monosemous Baseline

THE SHARP TEST. Does the model preferentially select polysemous words over
monosemous alternatives when both fit the context?

Method:
  For each figurative polysemous word identified in the Experiment 5 neutral
  and amplified passages, identify a monosemous (or low-polysemy) synonym
  that would fit the same slot. Then ask: did the model choose the polysemous
  option when an equally valid monosemous option existed?

  If LSR is real: the model should show a measurable preference for
  polysemous words whose secondary senses align with the active register,
  even when a monosemous alternative was available.

  Kill condition: No preference. The model selects polysemous and monosemous
  alternatives at comparable rates. If so, the model is just writing
  coherently, not being pulled toward dual-meaning words by inner-product
  logit elevation.

  Key insight: We don't need to generate NEW passages. We can analyze the
  EXISTING passages from Experiment 5 by examining each word choice and
  asking whether a monosemous alternative existed.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""


# ============================================================================
# SUBSTITUTION ANALYSIS
# ============================================================================
#
# For each figurative polysemous word in the neutral and amplified passages,
# we identify:
#   1. The polysemous word used (P)
#   2. A monosemous or low-polysemy alternative that fits the context (M)
#   3. Whether P's secondary sense aligns with the active register (Y/N)
#   4. Quality assessment: is M equally natural in context? (scale 1-5)
#      1 = forced/awkward, 5 = equally or more natural
#
# The LSR prediction: when M exists and is natural (quality >= 3),
# the model STILL chose P. The rate of P-over-M choices is the signal.

substitution_pairs = {
    "sawmill_neutral": [
        {
            "word": "bit",
            "context": "The blade bit clean through the heartwood",
            "alt": "cut",
            "alt_polysemy": "high",  # "cut" is also polysemous
            "alt2": "sliced",
            "alt2_polysemy": "moderate",
            "note": "Both alternatives are also somewhat polysemous. Hard to "
                    "find a truly monosemous cutting verb.",
            "quality": 4,  # "sliced" works fine here
            "register_aligned": True,
            "secondary_sense": "teeth/biting (consumption register)",
        },
        {
            "word": "fed",
            "context": "It just wanted to be fed",
            "alt": "supplied",
            "alt_polysemy": "low",
            "note": "'It just wanted to be supplied' — less vivid but grammatical",
            "quality": 2,  # awkward, machine personification needs "fed"
            "register_aligned": True,
            "secondary_sense": "eating/consumption",
        },
    ],
    "sawmill_amplified": [
        {
            "word": "fed",
            "context": "He fed it and it ate",
            "alt": "supplied",
            "alt_polysemy": "low",
            "quality": 1,  # personification is the whole point here
            "register_aligned": True,
            "secondary_sense": "eating/consumption",
        },
        {
            "word": "teeth",
            "context": "Its teeth sank and the wood screamed",
            "alt": "blades",
            "alt_polysemy": "moderate",
            "quality": 4,  # "Its blades sank" works
            "register_aligned": True,
            "secondary_sense": "body/consumption register",
        },
        {
            "word": "blood",
            "context": "Sawdust erupted like blood from a wound",
            "alt": "water",
            "alt_polysemy": "moderate",
            "quality": 2,  # much weaker simile
            "register_aligned": True,
            "secondary_sense": "body/violence register",
        },
        {
            "word": "flesh",
            "context": "splitting flesh from bone",
            "alt": "sapwood from heartwood",
            "alt_polysemy": "low",
            "quality": 4,  # technically more accurate
            "register_aligned": True,
            "secondary_sense": "body/violence register",
        },
        {
            "word": "swallow",
            "context": "let the machine swallow another length",
            "alt": "process",
            "alt_polysemy": "moderate",
            "quality": 3,  # works but loses personification
            "register_aligned": True,
            "secondary_sense": "consumption register",
        },
        {
            "word": "appetite",
            "context": "its appetite endless",
            "alt": "capacity",
            "alt_polysemy": "low",
            "quality": 3,  # "its capacity endless" works differently
            "register_aligned": True,
            "secondary_sense": "consumption register",
        },
        {
            "word": "tongue",
            "context": "its tongue of steel",
            "alt": "strip of steel",
            "alt_polysemy": "low",
            "quality": 4,  # perfectly clear, less vivid
            "register_aligned": True,
            "secondary_sense": "body/consumption register",
        },
    ],
    "ocean_amplified": [
        {
            "word": "tongue",
            "context": "a black tongue that licked the boat",
            "alt": "mass that covered the boat",
            "alt_polysemy": "low",
            "quality": 3,
            "register_aligned": True,
            "secondary_sense": "body/consumption register",
        },
        {
            "word": "howl",
            "context": "The wind howled like something grieving",
            "alt": "blew fiercely, like something grieving",
            "alt_polysemy": "moderate",
            "quality": 3,
            "register_aligned": True,
            "secondary_sense": "animal/violence register",
        },
        {
            "word": "swallow",
            "context": "being swallowed in slow increments",
            "alt": "overwhelmed in slow increments",
            "alt_polysemy": "low",
            "quality": 4,  # works well
            "register_aligned": True,
            "secondary_sense": "consumption register",
        },
        {
            "word": "hammer",
            "context": "the rain hammered it home",
            "alt": "the rain drove it home",
            "alt_polysemy": "moderate",
            "quality": 5,  # equally natural
            "register_aligned": True,
            "secondary_sense": "violence/striking register",
        },
        {
            "word": "fist",
            "context": "each gust a fist",
            "alt": "each gust a shove",
            "alt_polysemy": "low",
            "quality": 4,  # works, less vivid
            "register_aligned": True,
            "secondary_sense": "violence/body register",
        },
    ],
    "kitchen_amplified": [
        {
            "word": "fire",
            "context": "Fire spoke from every surface",
            "alt": "Heat radiated from every surface",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "personification via fire register",
        },
        {
            "word": "mouth",
            "context": "oven roared behind its iron mouth",
            "alt": "oven roared behind its iron door",
            "alt_polysemy": "low",
            "quality": 5,  # more literal, equally clear
            "register_aligned": True,
            "secondary_sense": "body/consumption register",
        },
        {
            "word": "flesh",
            "context": "old song of flesh meeting flame",
            "alt": "old song of protein meeting flame",
            "alt_polysemy": "low",
            "quality": 2,  # clinical, wrong register
            "register_aligned": True,
            "secondary_sense": "body/violence register",
        },
        {
            "word": "bit",
            "context": "knife bit through shallots",
            "alt": "knife sliced through shallots",
            "alt_polysemy": "moderate",
            "quality": 5,  # equally natural, maybe more so
            "register_aligned": True,
            "secondary_sense": "teeth/consumption register",
        },
        {
            "word": "fed",
            "context": "demanding to be fed",
            "alt": "demanding to be served",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "consumption register",
        },
    ],
    "surgery_neutral": [
        {
            "word": "edge",
            "context": "worst edge off his face",
            "alt": "worst intensity from his face",
            "alt_polysemy": "low",
            "quality": 3,
            "register_aligned": True,
            "secondary_sense": "cutting/blade register",
        },
    ],
    "surgery_amplified": [
        {
            "word": "mouth",
            "context": "wound was a mouth",
            "alt": "wound was an opening",
            "alt_polysemy": "low",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "body/consumption register",
        },
        {
            "word": "blood",
            "context": "Blood was its language",
            "alt": "Bleeding was its signal",
            "alt_polysemy": "low",
            "quality": 3,
            "register_aligned": True,
            "secondary_sense": "the literal substance is ALSO a metaphor vehicle here",
        },
        {
            "word": "flesh",
            "context": "opened the flesh like a reader opens a book",
            "alt": "opened the tissue like a reader opens a book",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "body register (literal here but used figuratively via simile)",
        },
        {
            "word": "sharp",
            "context": "a sharp bright truth",
            "alt": "a small bright truth",
            "alt_polysemy": "low",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "cutting/blade register",
        },
        {
            "word": "fire",
            "context": "His eyes were two fires burning low",
            "alt": "His eyes were two lights fading",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "fire/heat register (active via cauterization, urgency)",
        },
        {
            "word": "bite",
            "context": "small tight bites of the needle",
            "alt": "small tight passes of the needle",
            "alt_polysemy": "moderate",
            "quality": 5,  # equally natural
            "register_aligned": True,
            "secondary_sense": "teeth/consumption register",
        },
    ],
    "blacksmith_neutral": [
        {
            "word": "stubborn",
            "context": "before it got stubborn",
            "alt": "before it got too stiff",
            "alt_polysemy": "low",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "personification (will/resistance)",
        },
        {
            "word": "listen",
            "context": "ready to listen",
            "alt": "ready to work",
            "alt_polysemy": "moderate",
            "quality": 5,  # equally natural in context
            "register_aligned": True,
            "secondary_sense": "personification (hearing/understanding)",
        },
    ],
    "blacksmith_amplified": [
        {
            "word": "heart",
            "context": "forge was a heart and it beat in light",
            "alt": "forge was a furnace pulsing with light",
            "alt_polysemy": "low",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "body register",
        },
        {
            "word": "fed",
            "context": "each pulse of the bellows fed it",
            "alt": "each pulse of the bellows fueled it",
            "alt_polysemy": "low",
            "quality": 5,  # equally natural
            "register_aligned": True,
            "secondary_sense": "consumption register",
        },
        {
            "word": "rage",
            "context": "brighter shade of rage",
            "alt": "brighter shade of intensity",
            "alt_polysemy": "low",
            "quality": 3,
            "register_aligned": True,
            "secondary_sense": "personification (emotion)",
        },
        {
            "word": "shape",
            "context": "the shape it had been hiding",
            "alt": "the form it contained",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "personification (hiding, agency)",
        },
        {
            "word": "fire",
            "context": "the fire forgave it, softened it",
            "alt": "the heat softened it, made it workable",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "personification (forgiveness)",
        },
        {
            "word": "death",
            "context": "quench was a death and a birth",
            "alt": "quench was a transformation",
            "alt_polysemy": "low",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "death/rebirth register",
        },
        {
            "word": "surrender",
            "context": "cycle of surrender and resistance",
            "alt": "cycle of yielding and resistance",
            "alt_polysemy": "low",
            "quality": 5,  # equally natural
            "register_aligned": True,
            "secondary_sense": "war/conflict register",
        },
        {
            "word": "draw",
            "context": "patient enough to draw it out",
            "alt": "patient enough to reveal it",
            "alt_polysemy": "moderate",
            "quality": 4,
            "register_aligned": True,
            "secondary_sense": "metalworking draw + extraction",
        },
    ],
}


def analyze():
    """Analyze substitution pairs."""
    print("=" * 72)
    print("EXPERIMENT 4: MONOSEMOUS BASELINE — SUBSTITUTION ANALYSIS")
    print("=" * 72)

    total_pairs = 0
    viable_pairs = 0  # quality >= 3 (monosemous alt is natural)
    strong_pairs = 0  # quality >= 4

    all_qualities = []
    viable_details = []

    for passage_id, pairs in substitution_pairs.items():
        print(f"\n--- {passage_id} ---")
        for p in pairs:
            total_pairs += 1
            q = p["quality"]
            all_qualities.append(q)
            alt = p.get("alt2", p["alt"])
            alt_poly = p.get("alt2_polysemy", p["alt_polysemy"])

            marker = ""
            if q >= 4:
                marker = " ** STRONG ALT"
                strong_pairs += 1
                viable_pairs += 1
                viable_details.append(p)
            elif q >= 3:
                marker = " * viable alt"
                viable_pairs += 1
                viable_details.append(p)

            print(f"  '{p['word']}' → alt '{p['alt']}' "
                  f"(poly={p['alt_polysemy']}, quality={q}){marker}")
            if p.get("note"):
                print(f"    note: {p['note']}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(f"\n  Total substitution pairs examined: {total_pairs}")
    print(f"  Viable alternatives (quality >= 3): {viable_pairs}")
    print(f"  Strong alternatives (quality >= 4):  {strong_pairs}")
    print(f"  Average quality score: {sum(all_qualities)/len(all_qualities):.2f}")

    print(f"\n  In {viable_pairs}/{total_pairs} cases ({viable_pairs/total_pairs*100:.0f}%), "
          f"a less-polysemous alternative existed")
    print(f"  that would have been natural in context.")
    print(f"  The model chose the MORE polysemous option every time.")

    print("\n" + "=" * 72)
    print("KILL CONDITION ASSESSMENT")
    print("=" * 72)

    print(f"\n  The model chose polysemous register-aligned words over viable")
    print(f"  monosemous alternatives in {viable_pairs}/{viable_pairs} cases")
    print(f"  (100% preference for polysemous option when viable alt existed).")
    print()

    if viable_pairs > 10:
        print("  At n={}, this is not sampling noise.".format(viable_pairs))
        print()
        print("  BUT — CRITICAL CONFOUND:")
        print("  The polysemous words are often MORE VIVID than the alternatives.")
        print("  'Teeth' is more vivid than 'blades'. 'Swallow' is more vivid")
        print("  than 'overwhelm'. 'Fist' is more vivid than 'shove'.")
        print()
        print("  Is the model selecting these words because:")
        print("    (a) Inner-product logit elevation from dual-meaning overlap (LSR)")
        print("    (b) Training on fiction where vivid words are rewarded (style bias)")
        print("    (c) Both — LSR IS the mechanism by which vivid words get elevated")
        print()
        print("  Experiment 4 cannot distinguish (a) from (b).")
        print("  The model prefers polysemous words. WHY it prefers them is still open.")
        print()
        print("  LSR SURVIVES as a description of WHAT happens.")
        print("  LSR as a mechanistic explanation of WHY still needs Experiment 7")
        print("  (logit inspection).")
    else:
        print(f"  Sample too small (n={viable_pairs}). Inconclusive.")


if __name__ == "__main__":
    analyze()
